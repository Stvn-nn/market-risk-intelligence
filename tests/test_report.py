"""Regression: exported reports must show charts without executing JavaScript."""
import base64
from io import BytesIO
import re
import unittest
from PIL import Image
from market_risk.analytics import price_metrics,anomaly_signals,risk_index
from market_risk.demo import demo_prices
from market_risk.report import export_report


class ReportTests(unittest.TestCase):
    def test_charts_are_valid_embedded_images_without_scripts(self):
        p=demo_prices('AAPL').iloc[-100:]
        b=demo_prices('SPY').iloc[-100:]
        metrics=price_metrics(p,b)
        signals=anomaly_signals(p)
        report=export_report('AAPL','SPY',p,b,metrics,signals,risk_index(metrics,signals),{'source':'Synthetic','synthetic':True})
        self.assertNotIn('<script',report.lower())
        images=re.findall(r'src="data:image/png;base64,([^"]+)"',report)
        self.assertEqual(len(images),2)
        for data in images:
            with Image.open(BytesIO(base64.b64decode(data,validate=True))) as img:
                self.assertGreaterEqual(img.width,1000)
                self.assertGreaterEqual(img.height,500)
                self.assertGreater(len(img.convert('RGB').getcolors(maxcolors=2_000_000)),100)
            with Image.open(BytesIO(base64.b64decode(data,validate=True))) as img:
                img.verify()
        self.assertIn('SYNTHETIC DEMONSTRATION',report)

    def test_report_without_benchmark_still_has_price_chart(self):
        p=demo_prices('AAPL').iloc[-100:]
        metrics=price_metrics(p)
        signals=anomaly_signals(p)
        report=export_report('AAPL','SPY',p,None,metrics,signals,risk_index(metrics,signals),{'source':'Synthetic','synthetic':True})
        self.assertEqual(report.count('src="data:image/png;base64,'),1)
        self.assertIn('Benchmark unavailable.',report)

if __name__=='__main__':
    unittest.main()
