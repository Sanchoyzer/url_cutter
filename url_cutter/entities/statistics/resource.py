from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from url_cutter.entities.statistics.model import Statistics
from url_cutter.entities.url.model import Url


class StatisticsResource:
    __slots__ = ('__weakref__', 'main_db')

    def __init__(self, main_db: Session) -> None:
        self.main_db = main_db

    def _get_url(self, uid: str) -> Optional[Url]:
        return self.main_db.query(Url).filter_by(uid=uid).first()

    def get_list_raw(self, uid: str) -> List[Statistics]:
        if not (url := self._get_url(uid=uid)):
            return []
        return self.main_db.query(Statistics).filter_by(url_id=url.id).order_by(Statistics.id).all()

    def get_list(self, uid: str) -> List[Dict]:
        if not (url := self._get_url(uid=uid)):
            return []
        return [
            i._asdict()
            for i in self.main_db.query(
                func.date_trunc('day', Statistics.created_at).label('create_date'),
                func.count(Statistics.id).label('click_count'),
            )
            .filter_by(url_id=url.id)
            .group_by('create_date')
            .order_by('create_date')
            .all()
        ]

    def update(self, uid: str, headers: List[Tuple[str, str]], client: Dict) -> Optional[int]:
        if not (url := self._get_url(uid=uid)):
            return None
        headers = {i[0]: i[1] for i in headers}
        stat = Statistics(url_id=url.id, user_agent=headers.get('user-agent'), host=client.get('host'))
        self.main_db.add(stat)
        self.main_db.commit()
        return stat.id
