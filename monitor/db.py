from peewee import SqliteDatabase, Model, IntegerField, BooleanField, CharField

db = SqliteDatabase("frenbridge.db")


class Metadata(Model):
    last_block = IntegerField()
    chain_id = CharField()
    relayer_id = IntegerField()

    class Meta:
        database = db


class Submitted(Model):
    tx_hash = IntegerField(null=True)
    source_chain_id = CharField()
    hashed_proposal = IntegerField(unique=True)
    success = BooleanField()

    class Meta:
        database = db

    def __str__(self):
        return f"Submitted<{self.tx_hash}>"


try:
    db.create_tables([Metadata, Submitted])
    m = Metadata.create(last_block=0)
    m.save()
except:
    pass
