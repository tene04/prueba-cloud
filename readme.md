docker run -d --name postgres-demo -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin123 -e POSTGRES_DB=demodb -p 5432:5432 postgres:15

docker exec -i postgres-demo psql -U admin -d demodb < init.sql

pip install -r requirements.txt

set PG_HOST=localhost& set PG_PORT=5432& set PG_DATABASE=demodb& set PG_USER=admin& set PG_PASSWORD=admin123& uvicorn main:app --reload --port 8080

en prueba poner sslmode="require" en main.py

npm install

npm run dev