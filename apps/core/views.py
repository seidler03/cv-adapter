from django.views.generic import TemplateView
from django.conf import settings


class HomeView(TemplateView):
    template_name = 'core/home.html'

    FEATURES = [
        ('\U0001f916', 'AI-Powered Rewriting', 'GPT-4o-mini rewrites your CV to perfectly match each job description.'),
        ('\U0001f511', 'Keyword Gap Analysis', 'Instantly see which keywords are present and which ones you are missing.'),
        ('\U00002709', 'Cover Letter Generator', 'Get a tailored cover letter referencing specific job requirements.'),
    ]

    STEPS = [
        {'title': 'Upload your base CV', 'desc': 'PDF or DOCX — we extract the text automatically.'},
        {'title': 'Paste the job description', 'desc': 'Copy the full JD from any job board.'},
        {'title': 'Click "Adapt My CV"', 'desc': 'AI rewrites your CV and generates a cover letter in seconds.'},
        {'title': 'Copy or download the result', 'desc': 'Download as DOCX or copy the text directly.'},
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pro_price'] = settings.PRO_PLAN_PRICE
        ctx['free_monthly'] = settings.FREE_PLAN_MONTHLY_LIMIT
        ctx['features'] = self.FEATURES
        ctx['steps'] = self.STEPS
        return ctx


class PricingView(TemplateView):
    template_name = 'core/pricing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pro_price'] = settings.PRO_PLAN_PRICE
        ctx['free_limit'] = settings.FREE_PLAN_MONTHLY_LIMIT
        return ctx
