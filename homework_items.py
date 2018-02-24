from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Subject, Base, Item, User

engine = create_engine('sqlite:///homeworkitems.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user

User1 = User(name="Melissa Cannon", email="cannon@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Homework Items for Math
subject1 = Subject(user_id=1, name="Math")

item1 = Item(user_id=1, name="Study for quiz", description="Review all the worksheets",
                     time_estimate="1 hour", priority="High", subject=subject1)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Daily math homework", description="1 through 35 odd",
                     time_estimate="20 min", priority="Medium", subject=subject1)

session.add(item2)
session.commit()

subject2 = Subject(user_id=1, name="Literature")

session.add(subject2)
session.commit()

item1 = Item(user_id=1, name="Intro and conclusion for poetry essay", description="Write draft",
                     time_estimate="2 hours", priority="Low", subject=subject2)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="R & J worksheet", description="Annotate a passage",
                     time_estimate="30 min", priority="High", subject=subject2)

session.add(item2)
session.commit()

subject3 = Subject(user_id=1, name="Chinese")

session.add(subject3)
session.commit()

item1 = Item(user_id=1, name="Study for character quiz", description="Due: next Monday",
                     time_estimate="45 min", priority="Low", subject=subject3)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Characters and sentences", description="Write Chinese characters and sentences",
                     time_estimate="30 min", priority="High", subject=subject3)

session.add(item2)
session.commit()

subject4 = Subject(user_id=1, name="Social Science")

session.add(subject4)
session.commit()

item1 = Item(user_id=1, name="Group project", description="Review assignment sheet",
                     time_estimate="30 min", priority="Medium", subject=subject4)

session.add(item1)
session.commit()

print "added homework items!"
