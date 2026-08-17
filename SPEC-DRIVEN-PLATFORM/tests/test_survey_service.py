import csv
from pathlib import Path

import pytest

from customer_health_platform import SurveyServiceAnalyzer


@pytest.fixture
def synthetic_survey_csv(tmp_path):
    rows = [
        {
            "Correo electrónico": "cliente.sintetico.0001@synthetic.test",
            "Tiempo utilizando el servicio": "1 a 2 años",
            "Frecuencia de uso/interacción": "Mensualmente",
            "Dificultad técnica, retraso o problema no resuelto reciente": "No",
            "Valor general en relación con el precio (1-5)": "5",
            "Rapidez y amabilidad en Soporte/Atención al Cliente": "Excelente",
            "Calidad del servicio entregado": "Bueno",
            "Cumplimiento de expectativas iniciales": "Excelente",
            "Cumplimiento de objetivos al contratar": "['Cumplió completamente']",
            "Probabilidad de recomendar (1-10)": "10",
            "Probabilidad de renovar/continuar próximos 3 meses": "Probable",
            "Razón principal si considera no continuar": "No he considerado abandonar el servicio.",
            "Cambio o mejora urgente para calificar 10/10": "Mejorar la atención y el seguimiento de los casos.",
        },
        {
            "Correo electrónico": "cliente.sintetico.0002@example.com",
            "Tiempo utilizando el servicio": "Menos de 3 meses",
            "Frecuencia de uso/interacción": "Diariamente",
            "Dificultad técnica, retraso o problema no resuelto reciente": "Sí",
            "Valor general en relación con el precio (1-5)": "2",
            "Rapidez y amabilidad en Soporte/Atención al Cliente": "Deficiente",
            "Calidad del servicio entregado": "Aceptable",
            "Cumplimiento de expectativas iniciales": "Aceptable",
            "Cumplimiento de objetivos al contratar": "['Cumplió completamente']",
            "Probabilidad de recomendar (1-10)": "3",
            "Probabilidad de renovar/continuar próximos 3 meses": "Poco probable",
            "Razón principal si considera no continuar": "Tiempos de respuesta de soporte.",
            "Cambio o mejora urgente para calificar 10/10": "Agregar más funcionalidades y opciones de personalización.",
        },
    ]

    csv_path = tmp_path / "encuesta_servicio.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


def test_survey_service_analyzer_reads_dataset(synthetic_survey_csv):
    analyzer = SurveyServiceAnalyzer()
    rows = analyzer.load_csv(synthetic_survey_csv)

    assert len(rows) == 2
    assert rows[0]["Correo electrónico"].startswith("cliente.sintetico.0001")


def test_survey_service_analyzer_builds_summary(synthetic_survey_csv):
    analyzer = SurveyServiceAnalyzer()
    summary = analyzer.analyze_file(synthetic_survey_csv)

    assert summary["total_records"] == 2
    assert "renewal_probability" in summary
    assert "nps_snapshot" in summary
    assert "top_issues" in summary
