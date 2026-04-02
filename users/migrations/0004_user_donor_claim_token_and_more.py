from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_alter_user_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="donor_claim_token",
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="donor_claim_token_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
