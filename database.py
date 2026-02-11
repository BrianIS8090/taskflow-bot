import sqlite3
from datetime import datetime
from typing import List, Optional, Dict


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_all_tasks(self, status: str = None) -> List[Dict]:
        """Получить все задачи или по статусу"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT id, title, description, deadline, status, created_at FROM task WHERE status = ? ORDER BY deadline",
                (status,)
            )
        else:
            cursor.execute(
                "SELECT id, title, description, deadline, status, created_at FROM task WHERE status != 'completed' ORDER BY deadline"
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "deadline": row[3],
                "status": row[4],
                "created_at": row[5]
            })
        
        return tasks
    
    def get_today_tasks(self) -> List[Dict]:
        """Получить задачи на сегодня"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = datetime.now().strftime("%Y-%m-%d") + " 23:59:59"
        
        cursor.execute(
            """SELECT id, title, description, deadline, status, created_at 
               FROM task 
               WHERE status != 'completed' 
               AND deadline >= ? 
               AND deadline <= ? 
               ORDER BY deadline""",
            (today + " 00:00:00", tomorrow)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "deadline": row[3],
                "status": row[4],
                "created_at": row[5]
            })
        
        return tasks
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Получить просроченные задачи"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            """SELECT id, title, description, deadline, status, created_at 
               FROM task 
               WHERE status = 'pending' 
               AND deadline < ? 
               ORDER BY deadline""",
            (now,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "deadline": row[3],
                "status": row[4],
                "created_at": row[5]
            })
        
        return tasks
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM task")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM task WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM task WHERE status = 'running'")
        running = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM task WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT COUNT(*) FROM task WHERE status = 'pending' AND deadline < ?", (now,))
        overdue = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "overdue": overdue
        }
    
    def create_task(self, title: str, description: str, deadline: datetime) -> int:
        """Создать задачу"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        deadline_str = deadline.strftime("%Y-%m-%d %H:%M:%S")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO task (title, description, deadline, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (title, description, deadline_str, created_at)
        )
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """Обновить статус задачи"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE task SET status = ? WHERE id = ?",
            (status, task_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_task(self, task_id: int) -> bool:
        """Удалить задачу"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM task WHERE id = ?", (task_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Получить задачу по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, description, deadline, status, created_at FROM task WHERE id = ?",
            (task_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "deadline": row[3],
                "status": row[4],
                "created_at": row[5]
            }
        
        return None
