from fastapi import Depends
from typing import Annotated
from typing import Annotated

from app.database.session import get_db
from app.core.unit_of_work import UnitOfWork



def get_uow(db = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(db)



UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_uow)]


