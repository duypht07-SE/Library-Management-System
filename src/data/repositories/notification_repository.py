from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import Notification


class NotificationRepository(BaseRepository):
    def find_for_reader(self, reader_id: int) -> list[Notification]:
        rows = self.db.fetch_all(
            "SELECT * FROM notifications WHERE reader_id = ? "
            "ORDER BY COALESCE(sent_at, '') DESC, notification_id DESC",
            (reader_id,))
        return [Notification.from_row(r) for r in rows]

    def create_sent(self, reader_id: int, message: str, at: datetime,
                    conn=None) -> Notification:
        note = Notification(None, reader_id, message)
        note.send(at)
        sql = ("INSERT INTO notifications "
               "(reader_id, channel, message, status, sent_at) "
               "VALUES (?, ?, ?, ?, ?)")
        params = (note.reader_id, note.channel.value, note.message,
                  note.status.value, note.sent_at.isoformat(sep=" "))
        if conn is not None:
            note.notification_id = int(conn.execute(sql, params).lastrowid)
            return note
        with self.db.transaction() as tx:
            note.notification_id = int(tx.execute(sql, params).lastrowid)
        return note

    def exists_message(self, reader_id: int, message: str, conn=None) -> bool:
        sql = ("SELECT 1 FROM notifications "
               "WHERE reader_id = ? AND message = ? LIMIT 1")
        if conn is not None:
            return conn.execute(sql, (reader_id, message)).fetchone() is not None
        return self.db.fetch_one(sql, (reader_id, message)) is not None

    def send_pending(self, at: datetime, conn=None) -> int:
        sql = ("UPDATE notifications SET status = 'SENT', sent_at = ? "
               "WHERE status = 'PENDING'")
        ts = at.isoformat(sep=" ")
        if conn is not None:
            return conn.execute(sql, (ts,)).rowcount
        with self.db.transaction() as tx:
            return tx.execute(sql, (ts,)).rowcount
