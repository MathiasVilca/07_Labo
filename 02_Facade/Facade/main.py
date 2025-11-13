import json
import datetime
import os
from pathlib import Path

class LoggingModule:
    def __init__(self,interpreter):
        self.interpreter=interpreter
    def resource(self):
        return {
            "null_resource": {
                "logging": {
                    "depends_on": ["null_resource.bucket_access"],
                    "provisioner": [{
                        "local-exec": {
                            "interpreter": [self.interpreter, "-c"],
                            "command": (
                                "import pathlib; "
                                "pathlib.Path('logs').mkdir(exist_ok=True); "
                                "open('logs/iac.log', 'w').write('Ejecución completa\\n')"
                            )
                        }
                    }]
                }
            }
        }

class StorageBucketModule:
    def __init__(self, name_base, buckets_dir="./buckets",interpreter="python3"):
        self.name = f"{name_base}-storage-bucket"
        self.path = buckets_dir
        self.created_at = str(datetime.datetime.now())
        self.interpreter = interpreter

    def resource(self):
        return {
            "null_resource": {
                "storage_bucket": {
                    "triggers": {"name": self.name, "path": self.path,"created_at": self.created_at},
                    "provisioner": [{
                        "local-exec": {
                            "interpreter": [self.interpreter, "-c"],
                            "command": (
                                f"import pathlib; "
                                f"pathlib.Path(r'{self.path}/{self.name}').mkdir(parents=True, exist_ok=True)"
                            )
                        }
                    }]
                }
            }
        }

    def outputs(self):
        return {"name": self.name, "path": self.path,"created_at": self.created_at}


class StorageBucketAccessModule:
    def __init__(self, bucket_facade, entity, role):
        self.bucket = bucket_facade #bucket_facade["name"]
        self.entity = entity
        self.role = role

    def resource(self):
        return {
            "null_resource": {
                "bucket_access": {
                    "triggers": {
                        "bucket": self.bucket["name"],
                        "entity": self.entity,
                        "role": self.role
                    },
                    "depends_on": ["null_resource.storage_bucket"],
                    "provisioner": [{
                        "local-exec": {
                            "interpreter": ["python3", "-c"],
                            "command": (
                                f"print('Acceso aplicado al bucket {self.bucket['name']} con path {self.bucket['path']} creado el {self.bucket['created_at']}')"
                            )
                        }
                    }]
                }
            }
        }
    

if __name__ == "__main__":
    base_name = os.getenv("BUCKET_NAME_BASE", "hello-world")
    bucket_mod = StorageBucketModule(base_name)
    bucket_facade = bucket_mod.outputs()

    access_mod = StorageBucketAccessModule(
        bucket_facade, "allAuthenticatedUsers", "READER"
    )

    log_mod = LoggingModule("python3")

    Path(".").mkdir(exist_ok=True)

    with open("bucket.tf.json", "w", encoding="utf-8") as f:
        json.dump({"resource": bucket_mod.resource()}, f, indent=2)

    with open("bucket_access.tf.json", "w", encoding="utf-8") as f:
        json.dump({"resource": access_mod.resource()}, f, indent=2)
    
    with open("logging.tf.json", "w", encoding="utf-8") as f:
        json.dump({"resource": log_mod.resource()}, f, indent=2)

    provider_conf = {
        "terraform": {
            "required_providers": {
                "null": {
                    "source": "hashicorp/null",
                    "version": "~> 3.2"
                }
            }
        },
        "provider": {
            "null": {}
        }
    }
    with open("provider.tf.json", "w", encoding="utf-8") as f:
        json.dump(provider_conf, f, indent=2)
