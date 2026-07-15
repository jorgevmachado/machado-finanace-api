import subprocess

container_name = "machado-finance-api_db"

database = "machadoFinanceDB"
user = "machado"
password = "machado"

output_file = "./migrations/backup.dump"

command = [
    "docker",
    "exec",
    "-e",
    f"PGPASSWORD={password}",
    container_name,
    "pg_dump",
    "-U",
    user,
    "-Fc",
    database,
]

with open(output_file, "wb") as f:
    subprocess.run(command, stdout=f, check=True)

print(f"Dump gerado com sucesso em: {output_file}")