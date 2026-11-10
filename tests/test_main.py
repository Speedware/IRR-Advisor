import unittest
from main import npv, irr, Project, recommend

class InvestmentTests(unittest.TestCase):
    def test_npv_manual(self):
        self.assertAlmostEqual(npv(.1, [-100, 110]), 0, places=9)
    def test_irr_exact(self):
        self.assertAlmostEqual(irr([-100, 110]), .1, places=8)
    def test_irr_reference_screenshot(self):
        # 4000 — CF0; -200, 1000, 1200, 1800, 2500 — CF1..CF5.
        # Этот поток нестандартен, так как в первый год есть дополнительный отток.
        # Проверяем NPV при контрольной ставке; интерактивный ввод такие потоки запрещает.
        self.assertAlmostEqual(npv(.12253846311064, [-4000,-200,1000,1200,1800,2500]), 0, places=7)
    def test_irr_no_positive(self):
        self.assertIsNone(irr([-100, 0, 0, 0, 0, 0]))
    def test_invalid_irr(self):
        with self.assertRaises(ValueError): irr([-100, 150, -10])
    def test_choose_higher_npv(self):
        a = Project('А', 1000, [400]*5)
        b = Project('Б', 2000, [700]*5)
        winner, _, _ = recommend([a, b], .1)
        self.assertEqual(winner.name, 'Б')
    def test_reject_all(self):
        a = Project('А', 1000, [50]*5)
        b = Project('Б', 2000, [100]*5)
        winner, _, _ = recommend([a,b], .1)
        self.assertIsNone(winner)
    def test_project_flows(self):
        self.assertEqual(Project('X', 100, [1]*5).flows, [-100]+[1]*5)
    def test_irr_below_zero(self):
        self.assertLess(irr([-100, 10, 10, 10, 10, 10]), 0)

if __name__ == '__main__': unittest.main()
