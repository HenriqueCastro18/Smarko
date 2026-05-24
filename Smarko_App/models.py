from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class LogSeguranca(models.Model):
    usuario_nome = models.CharField(max_length=255, default='sistema')
    evento = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario_nome} - {self.evento}"

class DataCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    retention_days = models.IntegerField(default=0, help_text="Dias de retenção (0 = indefinido)")

    class Meta:
        verbose_name_plural = "Data Categories"

    def __str__(self):
        return self.name

class DataPurpose(models.Model):
    LEGAL_BASIS_CHOICES = [
        ('consent', 'Consentimento'),
        ('contract', 'Contrato'),
        ('legal', 'Obrigação Legal'),
        ('vital', 'Proteção da Vida'),
        ('public', 'Interesse Público'),
        ('legitimate', 'Interesse Legítimo'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    legal_basis = models.CharField(max_length=20, choices=LEGAL_BASIS_CHOICES)
    categories = models.ManyToManyField(DataCategory, related_name='purposes')
    is_mandatory = models.BooleanField(default=True, help_text="Se obrigatório para usar a app")

    def __str__(self):
        return self.name

class ConsentRecord(models.Model):
    firebase_uid = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()
    version = models.IntegerField(default=1)

    purposes = models.ManyToManyField(DataPurpose, related_name='consent_records')

    given_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    accepted_terms = models.BooleanField(default=False)
    accepted_privacy = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-given_at']
        indexes = [
            models.Index(fields=['firebase_uid', '-given_at']),
            models.Index(fields=['email', 'is_active']),
        ]

    def __str__(self):
        status = "revogado" if self.revoked_at else "ativo"
        return f"{self.email} - v{self.version} ({status})"

    def is_valid(self):
        return self.revoked_at is None and self.is_active

class ConsentVersion(models.Model):
    version = models.IntegerField(unique=True)
    effective_date = models.DateTimeField()
    privacy_policy_hash = models.CharField(max_length=64, help_text="SHA256 hash da política")
    changes_summary = models.TextField()

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"Versão {self.version} ({self.effective_date.date()})"

class AccountDeletionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('canceled', 'Cancelado'),
        ('completed', 'Completado'),
    ]

    firebase_uid = models.CharField(max_length=255)
    email = models.EmailField()

    requested_at = models.DateTimeField(auto_now_add=True)
    deletion_scheduled_for = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_token = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['firebase_uid', 'status']),
            models.Index(fields=['confirmation_token']),
        ]

    def __str__(self):
        return f"{self.email} - {self.get_status_display()}"

    def is_overdue(self):
        return self.status == 'pending' and timezone.now() >= self.deletion_scheduled_for