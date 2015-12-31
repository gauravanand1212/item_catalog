from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import datetime
 
Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('category_id', Integer, ForeignKey('category.id')),
    Column('item_id', Integer, ForeignKey('item.id'))
)

class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    items = relationship('Items',
             secondary=association_table,lazy="dynamic",backref='categories')

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
           'items'        : ([item.serialize for item in self.items])
       }
 
class Items(Base):
    __tablename__ = 'item'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(1000))
    updated = Column(DateTime, default=datetime.datetime.utcnow)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'           : self.id,
           'name'         : self.name,
           'description'  : self.description,

       }



engine = create_engine('sqlite:///itemcatalog.db')
 

Base.metadata.create_all(engine)