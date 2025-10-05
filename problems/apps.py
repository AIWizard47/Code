from django.apps import AppConfig


class ProblemsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "problems"

    def ready(self):
        print("✅ Problems app ready, starting scheduler...")
        from apscheduler.schedulers.background import BackgroundScheduler
        from django.utils.timezone import now

        def delete_problem_variants_job():
            from .models import ProblemVariant   # ✅ Import here, not at the top
            ProblemVariant.objects.all().delete()
            print(f"Deleted Problem Variants at {now()}")

        scheduler = BackgroundScheduler()
        scheduler.add_job(delete_problem_variants_job, "cron", hour=0, minute=0)
        scheduler.start()
