import unittest

from tools.analyze.build_forward_v1_hydraulic_unblock_plan_execution import (
    build_sensor_policy,
    parse_sacct,
    parse_squeue,
)


class ForwardV1HydraulicUnblockTests(unittest.TestCase):
    def test_parse_squeue_pipe_rows(self):
        rows = parse_squeue("3293924|NuclearEnergy|saltq_sel_cont|RUNNING|1-14:47:23|c318-016\n")
        self.assertEqual(rows[0]["job_id"], "3293924")
        self.assertEqual(rows[0]["state"], "RUNNING")
        self.assertEqual(rows[0]["node_or_reason"], "c318-016")

    def test_parse_sacct_pipe_rows(self):
        rows = parse_sacct("3295901|upc_pm5q|CANCELLED|0:0|00:00:00|None assigned\n")
        self.assertEqual(rows[0]["state"], "CANCELLED")
        self.assertEqual(rows[0]["exit_code"], "0:0")

    def test_sensor_policy_empty_input(self):
        class FakeRoot:
            def __truediv__(self, _other):
                return self

            def exists(self):
                return False

        self.assertEqual(build_sensor_policy(FakeRoot()), [])


if __name__ == "__main__":
    unittest.main()
