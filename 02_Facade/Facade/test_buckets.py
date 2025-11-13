import json
import os
import pytest
import subprocess

@pytest.fixture(scope="session", autouse=True)
def exec_main():
    subprocess.run(["python3", "main.py"], check=True)
    subprocess.run(["bash", "-c","terraform init"], check=True)
    subprocess.run(["bash", "-c","terraform apply --auto-approve"], check=True)
    yield
    subprocess.run(["bash", "-c","terraform destroy --auto-approve"], check=True)

def test_bucket_files_exist():
    for f in ["bucket.tf.json", "bucket_access.tf.json"]:
        assert os.path.exists(f)

def test_bucket_structure():
    data = json.load(open("bucket.tf.json"))
    assert "resource" in data
    assert "storage_bucket" in data["resource"]["null_resource"]

def test_access_depends_on_bucket():
    data = json.load(open("bucket_access.tf.json"))
    assert "depends_on" in data["resource"]["null_resource"]["bucket_access"]
    assert "null_resource.storage_bucket" in data["resource"]["null_resource"]["bucket_access"]["depends_on"]

TEST_NAMES=["bucket_name","bucket_name_2"]

@pytest.mark.parametrize("test_name",TEST_NAMES)
def test_modify_base_name(test_name):
    env = os.environ.copy()
    env["BUCKET_NAME_BASE"] = test_name
    subprocess.run(["python3", "main.py"], check=True, env=env)
    with open("bucket.tf.json") as f:
        data_bucket = json.load(f)
    trigger_bucket = data_bucket["resource"]["null_resource"]["storage_bucket"]["triggers"]["name"]
    with open("bucket_access.tf.json") as f:
        data_bucket = json.load(f)
    trigger_bucket_access = data_bucket["resource"]["null_resource"]["bucket_access"]["triggers"]["bucket"]
    assert trigger_bucket==trigger_bucket_access