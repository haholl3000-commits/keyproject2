import hashlib
import base64
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from .models import Document, UserProfile, ActionLog  # Добавили ActionLog


# 1. Главная страница
def dashboard(request):
    user_logs = []
    if request.user.is_authenticated:
        all_documents = Document.objects.filter(owner=request.user)
        # Получаем 5 последних действий для профиля
        user_logs = ActionLog.objects.filter(user=request.user)[:5]
    else:
        all_documents = []

    return render(request, 'documents/index.html', {
        'docs': all_documents,
        'user_logs': user_logs  # Передаем логи в шаблон
    })


# 3. Генерация ключей ЭЦП
@login_required
def generate_keys(request):
    user = request.user
    try:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.public_key = public_pem.decode('utf-8')
        profile.save()

        # ЗАПИСЬ В ЛОГ
        ActionLog.objects.create(
            user=user,
            action="Выпуск ЭЦП",
            details="Сгенерирована новая пара ключей RSA-2048"
        )

        messages.success(request, "ЭЦП успешно создана! Ключ в профиле, приватный файл загружен.")

        response = HttpResponse(private_pem, content_type='application/x-pem-file')
        response['Content-Disposition'] = 'attachment; filename="private_key.pem"'
        return response
    except Exception as e:
        messages.error(request, f"Ошибка при генерации ключей: {e}")
        return redirect('dashboard')


# 4. Подписание документа
@login_required
def sign_document(request, doc_id):
    if request.method == 'POST':
        document = get_object_or_404(Document, id=doc_id, owner=request.user)
        key_file = request.FILES.get('key_file')

        if not key_file:
            messages.error(request, "Выберите файл ключа (.pem)")
            return redirect('dashboard')

        try:
            private_key = serialization.load_pem_private_key(key_file.read(), password=None)

            with open(document.file.path, "rb") as f:
                file_content = f.read()

            file_hash = hashlib.sha256(file_content).hexdigest()

            signature = private_key.sign(
                file_content,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )

            document.file_hash = file_hash
            document.digital_signature = base64.b64encode(signature).decode('utf-8')
            document.status = 'signed'
            document.save()

            # ЗАПИСЬ В ЛОГ
            ActionLog.objects.create(
                user=request.user,
                action="Подписание",
                details=f"Документ: {document.title}"
            )

            messages.success(request, f"Документ '{document.title}' успешно подписан!")

        except Exception as e:
            # Логируем даже ошибку, это важно для аудита
            ActionLog.objects.create(
                user=request.user,
                action="Ошибка подписи",
                details=f"Неудачная попытка для файла: {document.title}"
            )
            messages.error(request, "Ошибка подписи: Возможно, ключ не подходит.")

    return redirect('dashboard')


# 5. Проверка подписи
@login_required
def verify_document(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    try:
        profile = UserProfile.objects.get(user=document.owner)
        public_key = serialization.load_pem_public_key(profile.public_key.encode('utf-8'))

        with open(document.file.path, "rb") as f:
            file_data = f.read()

        signature = base64.b64decode(document.digital_signature)

        public_key.verify(
            signature,
            file_data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

        # ЗАПИСЬ В ЛОГ
        ActionLog.objects.create(
            user=request.user,
            action="Верификация",
            details=f"Успешная проверка подписи файла: {document.title}"
        )

        return render(request, 'documents/verify.html', {'status': 'success', 'doc': document})

    except Exception as e:
        # Логируем неудачную проверку
        ActionLog.objects.create(
            user=request.user,
            action="Ошибка верификации",
            details=f"Подпись файла {document.title} не прошла проверку"
        )
        return render(request, 'documents/verify.html', {'status': 'error', 'doc': document})