# Generated by Django 5.2 on 2025-06-24 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movimentacao', '0002_alter_movimentacao_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimentacao',
            name='data',
            field=models.DateField(verbose_name='Data da Movimentação'),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='imposto_renda',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Imposto de Renda [Sim/Não]'),
        ),
    ]
