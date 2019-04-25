import pytest
import os
from pyggi.base import Patch, StatusCode, ParseError
from pyggi.line import LineProgram, LineDeletion
from pyggi.tree import TreeProgram, StmtInsertion

class MyLineProgram(LineProgram):
    def compute_fitness(self, elapsed_time, stdout, stderr):
        import re
        m = re.findall("runtime: ([0-9.]+)", stdout)
        if len(m) > 0:
            runtime = m[0]
            failed = re.findall("([0-9]+) failed", stdout)
            pass_all = len(failed) == 0
            failed = int(failed[0]) if not pass_all else 0
            return failed
        else:
            raise ParseError

class MyTreeProgram(TreeProgram):
    def compute_fitness(self, elapsed_time, stdout, stderr):
        import re
        m = re.findall("runtime: ([0-9.]+)", stdout)
        if len(m) > 0:
            runtime = m[0]
            failed = re.findall("([0-9]+) failed", stdout)
            pass_all = len(failed) == 0
            failed = int(failed[0]) if not pass_all else 0
            return failed
        else:
            raise ParseError

@pytest.fixture(scope='session')
def setup_line():
    line_program = MyLineProgram('../sample/Triangle_bug_python')
    return line_program

@pytest.fixture(scope='session')
def setup_tree():
    tree_program = MyTreeProgram('../sample/Triangle_bug_python')
    return tree_program

def check_program_validity(program):
    assert not program.path.endswith('/')
    assert program.name == os.path.basename(program.path)
    assert program.test_command is not None
    assert program.target_files is not None
    assert all([program.engines[target_file] is not None
        for target_file in program.target_files])
    assert all([program.modification_points[target_file] is not None
        for target_file in program.target_files])
    assert os.path.exists(program.tmp_path)

class TestLineProgram(object):

    def test_init(self, setup_line):
        program = setup_line
        check_program_validity(program)

    def test_init_with_config_file_name(self):
        program = LineProgram('../sample/Triangle_bug_python', config='.pyggi.config')
        check_program_validity(program)

    def test_init_with_dict_type_config(self):
        target_files = ["triangle.py"]
        test_command = "./run.sh"
        config = {
            "target_files": target_files,
            "test_command": test_command
        }

        program = LineProgram('../sample/Triangle_bug_python', config=config)
        check_program_validity(program)
        assert program.test_command == test_command
        assert program.target_files == target_files

    def test_tmp_path(self, setup_line):
        program = setup_line

        assert program.tmp_path.startswith(os.path.join(program.TMP_DIR, program.name))

    def test_create_tmp_variant(self, setup_line):
        program = setup_line
        assert os.path.exists(program.tmp_path)

    def test_load_contents(self, setup_line):
        program = setup_line
        assert 'triangle.py' in program.contents
        assert len(program.contents['triangle.py']) > 0

    def test_set_weight(self, setup_line):
        program = setup_line
        assert 'triangle.py' not in program.modification_weights
        program.set_weight('triangle.py', 1, 0.1)
        assert 'triangle.py' in program.modification_weights
        assert program.modification_weights['triangle.py'][1] == 0.1

    def test_get_source(self, setup_line):
        program = setup_line
        file_contents = open(os.path.join(program.tmp_path, 'triangle.py'), 'r').read()
        for i in range(len(program.modification_points['triangle.py'])):
            program.get_source('triangle.py', i) in file_contents

    def test_apply(self, setup_line):
        program = setup_line
        patch = Patch(program)
        patch.add(LineDeletion(('triangle.py', 1)))
        program.apply(patch)
        file_contents = open(os.path.join(program.tmp_path, 'triangle.py'), 'r').read()
        assert file_contents == program.dump(program.get_modified_contents(patch), 'triangle.py')

    def test_exec_cmd(self, setup_line):
        program = setup_line
        result = program.exec_cmd("echo hello")
        assert result.stdout.strip() == "hello"

    def test_evaluate_patch(self, setup_line):
        program = setup_line
        patch = Patch(program)
        status_code, fitness = program.evaluate_patch(patch)
        assert status_code == StatusCode.NORMAL
        assert fitness is not None


class TestTreeProgram(object):

    def test_init(self, setup_tree):
        program = setup_tree
        check_program_validity(program)

    def test_init_with_config_file_name(self):
        program = MyTreeProgram('../sample/Triangle_bug_python', config='.pyggi.config')
        check_program_validity(program)

    def test_init_with_dict_type_config(self):
        target_files = ["triangle.py"]
        test_command = "./run.sh"
        config = {
            "target_files": target_files,
            "test_command": test_command
        }

        program = MyTreeProgram('../sample/Triangle_bug_python', config=config)
        check_program_validity(program)
        assert program.test_command == test_command
        assert program.target_files == target_files

    def test_tmp_path(self, setup_tree):
        program = setup_tree

        assert program.tmp_path.startswith(os.path.join(program.TMP_DIR, program.name))

    def test_create_tmp_variant(self, setup_tree):
        program = setup_tree
        assert os.path.exists(program.tmp_path)

    def test_load_contents(self, setup_tree):
        program = setup_tree
        assert 'triangle.py' in program.contents
        assert program.contents['triangle.py'] is not None

    def test_set_weight(self, setup_tree):
        program = setup_tree
        assert 'triangle.py' not in program.modification_weights
        program.set_weight('triangle.py', 1, 0.1)
        assert 'triangle.py' in program.modification_weights
        assert program.modification_weights['triangle.py'][1] == 0.1

    def test_get_source(self, setup_tree):
        program = setup_tree
        file_contents = open(os.path.join(program.tmp_path, 'triangle.py'), 'r').read()
        for i in range(len(program.modification_points['triangle.py'])):
            program.get_source('triangle.py', i) in file_contents

    def test_apply(self, setup_tree):
        program = setup_tree
        patch = Patch(program)
        patch.add(StmtInsertion(('triangle.py', 1), ('triangle.py', 10), direction='after'))
        program.apply(patch)
        file_contents = open(os.path.join(program.tmp_path, 'triangle.py'), 'r').read()
        assert file_contents == program.dump(program.get_modified_contents(patch), 'triangle.py')

    def test_exec_cmd(self, setup_tree):
        program = setup_tree
        result = program.exec_cmd("echo hello")
        assert result.stdout.strip() == "hello"

    def test_evaluate_patch(self, setup_tree):
        program = setup_tree
        patch = Patch(program)
        status_code, fitness = program.evaluate_patch(patch)
        assert status_code == StatusCode.NORMAL
        assert fitness is not None