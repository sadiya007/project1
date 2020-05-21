import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# database engine object from SQLAlchemy that manages connections to the database
engine = create_engine(
    "postgres://htidpfuklxnnyf:ac4404e1db48ddaf2b31f906e8c5d1ade2cb5859dc30da15c7382d77cfcb7453@ec2-52-6-143-153.compute-1.amazonaws.com:5432/den3qj7mugr7k2")
db = scoped_session(sessionmaker(bind=engine))

# create a 'scoped session' that ensures different users' interactions with the
# database are kept separate
db = scoped_session(sessionmaker(bind=engine))

file = open("books.csv")

reader = csv.reader(file)

#db.execute("CREATE TABLE mybooks(books_id SERIAL PRIMARY KEY, isbn VARCHAR, title VARCHAR, author VARCHAR, yearsofissue INTEGER) ")

for isbn, title, author, year in reader:
    db.execute(
        "INSERT INTO mybooks (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn, "title": title, "author": author, "year": year},
    )
    print(f"Added book {title} to database.")
    db.commit()
