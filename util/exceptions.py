class ORMException(Exception):
    def __init__(self, table: str, *args: object) -> None:
        super().__init__(*args)
        self.table = table

    def __str__(self) -> str:
        return f"ORM ERROR: Table {self.table}\n{super().__str__()}"
    
class ORMRegistryError(ORMException):
    def __str__(self) -> str:
        return f"ORM REGISTRY ERROR: Table {self.table} is not registered\n{super().__str__()}"