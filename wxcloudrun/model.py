from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())

# 景点列表
class Spot(db.Model):
    __tablename__ = 'Spot'
    
    spot_id = db.Column(db.Integer, primary_key=True)
    spot_name = db.Column(db.Text, nullable=False)
    s_weiyi = db.Column(db.BigInteger, nullable=False, default=1)
    s_lishi = db.Column(db.BigInteger, nullable=False, default=1)
    s_ziran = db.Column(db.BigInteger, nullable=False, default=1)
    s_yule = db.Column(db.BigInteger, nullable=False, default=1)
    s_guanguang = db.Column(db.BigInteger, nullable=False, default=1)
    link = db.Column(db.Text)
    image = db.Column(db.Text)
    city = db.Column(db.Text)
    address = db.Column(db.Text)
    tour_time = db.Column(db.Float)
    info = db.Column(db.Text)
    keyword1 = db.Column(db.Text)
    keyword2 = db.Column(db.Text)
    keyword3 = db.Column(db.Text)
    keyword4 = db.Column(db.Text)
    keyword5 = db.Column(db.Text)
    pos = db.Column(db.Text)
    hotness = db.Column(db.BigInteger)
