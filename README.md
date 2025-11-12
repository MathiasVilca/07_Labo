### NOTA: Este repositorio se creo originalmente el 9/10, pero por un error el repositorio se elimino
### NOTA 2: Los archivos relevantes se incluiran en las carpetas con el nombre de cada seccion de laboratorio, las cuales se añadiran poco a poco
## Adapter
1. Se podria garantizar la validez del contrato definiendo una interfaz para los Adaptadores, la cual los obligue a definir un metodo `outputs()`. Respecto a pruebas unitarias, se puede probar que la salida del método `outputs()` es la esperada (en este caso, un array de tuplas de tres strings cada una) haciendo uso de `@pytest.mark.parametrize` para definir varios casos y sus salidas esperadas

2. La complejidad temporal de LocalIdentityAdapter tiene de líneas relevantes:
```python
for permission, users in metadata.items():
            for user in users:
                # Mantener la misma estructura de tupla para outputs
                self.local_users.append((user, user, permission))
```
El primer bucle se ejecuta R veces (al ser R pares en diccionario `metadata`) y el segundo se ejecuta N veces, donde n es el número de usuarios en dicho rol, si consideramos las veces totales que se va a ejecutar `append()`, la complejidad es de **O(U)**.  
Mientras tanto, al guardarse una tupla por usuario, tiene una complejidad espacial de **O(U)**
De forma similar, en LocalProjectUsers:
```python
for (user, identity, role) in self._users:
            # Nombre único de recurso
            res_name = f"identity_{user}_{role}".replace('-', '_')
            resources.append({
                "null_resource": {
                    res_name: {
                        "triggers": {
                            "user": user,
                            "identity": identity,
                            "role": role
                        }
                    }
                }
            })
```
Este for se ejecuta por cada tupla, y como el numero de tuplas es igual al numero de usuarios, la complejidad temporal es de **O(U)**. 
Mientras tanto, al guardarse una tupla por usuario, tiene una complejidad espacial de **O(U)**.  
Si hablamos de como escalaría, pues en si las complejidades solo dependen del numero total de usuarios (U), asi que tanto el tiempo y memoria se duplicarian

3. Propongo el siguiente adaptador YAML
```python
class yamlLocalIdentityAdapter:
    def __init__(self, metadata):
        self.local_users = []
        for permission, users in metadata.items():
            for user in users:
                # Mantener la misma estructura de tupla para outputs
                self.local_users.append((user, user, permission))

    def outputs(self):
        return self.local_users
    
    def _build(self):
        resources = []
        for (user, identity, role) in self.local_users:
            # Nombre único de recurso
            res_name = f"identity_{user}_{role}".replace('-', '_')
            resources.append({
                "null_resource": {
                    res_name: {
                        "triggers": {
                            "user": user,
                            "identity": identity,
                            "role": role
                        }
                    }
                }
            })
        
        data = {"resource": resources}
        
        with open("main.tf.yaml", "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
```

Posee una estructura idéntica al `LocalIdentityAdapter`, tiene los mismos atributos y la misma función de inicialización y `outputs()`, siguiendo el mismo contrato. La única diferencia es el método `_build()`, el cual funciona de manera similar al método del mismo nombre presente en `LocalProjectUsers`, solo que este tiene una función extra al final, la cual escribe los datos de usuarios guardados en `local_users` en el archivo `main.tf.yaml`
4. Se creó el siguiente adaptador:
```python
class AWSIdentityAdapter:
    def __init__(self, metadata):
        self.local_users = []
        for policy, users in metadata.items():
            for user in users:
                # Mantener la misma estructura de tupla para outputs
                # Genera iam
                id=randint(1000,9999)
                arn=f"arn:aws:iam::{id}"
                if "team" in user:
                    arn += f":group/{user}"
                elif "automation" in user:
                    arn += f":role/{user}"
                elif "user" in user:
                    arn += f":user/{user}"
                else:
                    arn += f":user/{user}"
                self.local_users.append((user, arn, policy))

    def outputs(self):
        return self.local_users
    
    def build(self):
        users = self.outputs()

        resources = {
            "null_resource": {}
        }

        for user, arn, policy in users:
            # User
            user_name = f"aws_iam_user_{user}".replace("-", "_")

            resources["null_resource"][user_name] = {
                "triggers": {
                    "user": user,
                    "arn": arn,
                }
            }

            # Policy attachment
            pol_name = f"aws_iam_policy_attachment_{user}_{policy}".replace("-", "_")

            resources["null_resource"][pol_name] = {
                "triggers": {
                    "user": user,
                    "arn": arn,
                    "policy": policy,
                }
            }

        data = {"resource": resources}

        with open("main.tf.json", "w") as outfile:
            json.dump(data, outfile, sort_keys=True, indent=4)
```

5. Se introduce este cambio de código:
```python
class LocalIdentityAdapter:
    """Adapter para transformar los roles genéricos a recursos locales null_resource."""
    def __init__(self, metadata):
        self.local_users = []
        for permission, users in metadata.items():
            if permission=="read": 
                permission="read_only"
            for user in users:
                # Mantener la misma estructura de tupla para outputs
                self.local_users.append((user, user, permission))

    def outputs(self):
        return self.local_users

```
El terraform detecta que la configuracion sigue siendo válida y no muestra cambios necesarios en el plan

6. Se creo el siguiente workflow, el cual estaria en .github/workflows/CICD.yml
```yaml
name: Pipeline simple

on:
  push:
  pull_request:

jobs:
  terraform:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout del repositorio
        uses: actions/checkout@v4

      - name: Instalar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Generate main.tf.json
        run: python main.py

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.5

      - name: Inicializar terraform
        run: terraform init -input=false

      - name: Ejecutar terraform validate
        run: terraform validate

      - name: Ejecutar terraform plan
        run: terraform plan

```

## Facade
1. 
 - Diagrama incluido en `02_Facade/`
 - Se usa Facade para desacople porque permite la independencia entre módulos (ahora se depende del facade), al uno estar separado del otro, no se usa Adapter porque este esta para adaptar (como indica su nombre) interfaces incompatibles, no "desacopla" nada.
 - Pros: El desacople, hacer cambios es más sencillo (en un solo lugar)  
   Contras: Se puede volver complejo de implementar si crece mucho
