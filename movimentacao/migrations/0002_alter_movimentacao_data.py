# Generated by Django 5.2 on 2025-06-24 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movimentacao', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimentacao',
            name='data',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação'),
        ),
    ]
