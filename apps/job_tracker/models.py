from django.db import models
from django.conf import settings


class JobApplication(models.Model):
    STATUS_APPLIED = 'applied'
    STATUS_SCREENING = 'screening'
    STATUS_INTERVIEW_1 = 'interview_1'
    STATUS_INTERVIEW_2 = 'interview_2'
    STATUS_TECHNICAL = 'technical'
    STATUS_OFFER = 'offer'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_GHOSTED = 'ghosted'

    STATUS_CHOICES = [
        (STATUS_APPLIED,     'Aplicado'),
        (STATUS_SCREENING,   'Triagem RH'),
        (STATUS_INTERVIEW_1, '1\u00aa Entrevista'),
        (STATUS_INTERVIEW_2, '2\u00aa Entrevista'),
        (STATUS_TECHNICAL,   'Teste T\u00e9cnico'),
        (STATUS_OFFER,       'Oferta Recebida'),
        (STATUS_REJECTED,    'Reprovado'),
        (STATUS_WITHDRAWN,   'Desist\u00eancia'),
        (STATUS_GHOSTED,     'Sem Retorno'),
    ]

    # Pipeline stages (positive progression), negative stays separate
    PIPELINE_STAGES = [
        STATUS_APPLIED, STATUS_SCREENING, STATUS_INTERVIEW_1,
        STATUS_INTERVIEW_2, STATUS_TECHNICAL, STATUS_OFFER,
    ]
    NEGATIVE_STAGES = [STATUS_REJECTED, STATUS_WITHDRAWN, STATUS_GHOSTED]

    STATUS_COLORS = {
        STATUS_APPLIED:     'bg-blue-900 text-blue-300',
        STATUS_SCREENING:   'bg-indigo-900 text-indigo-300',
        STATUS_INTERVIEW_1: 'bg-purple-900 text-purple-300',
        STATUS_INTERVIEW_2: 'bg-violet-900 text-violet-300',
        STATUS_TECHNICAL:   'bg-amber-900 text-amber-300',
        STATUS_OFFER:       'bg-green-900 text-green-300',
        STATUS_REJECTED:    'bg-red-900 text-red-300',
        STATUS_WITHDRAWN:   'bg-gray-700 text-gray-300',
        STATUS_GHOSTED:     'bg-orange-900 text-orange-300',
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tracked_applications',
    )
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    job_description = models.TextField(blank=True)
    cv_adaptation = models.ForeignKey(
        'cv_adapter.JobApplication',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tracker_entries',
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_APPLIED)
    data_aplicacao = models.DateField(auto_now_add=True)
    data_atualizacao = models.DateField(auto_now=True)
    link_vaga = models.URLField(blank=True)
    notas = models.TextField(blank=True)
    salario_estimado = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tracked Application'
        verbose_name_plural = 'Tracked Applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_title} @ {self.company} ({self.get_status_display()})"

    @property
    def status_badge_class(self):
        return self.STATUS_COLORS.get(self.status, 'bg-gray-700 text-gray-300')

    @property
    def pipeline_step(self):
        """0-based index in pipeline, or -1 if negative stage."""
        if self.status in self.PIPELINE_STAGES:
            return self.PIPELINE_STAGES.index(self.status)
        return -1
