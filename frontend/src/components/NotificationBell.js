import React, { useEffect, useState } from "react";
import { listNotifications, markAllRead } from "../services/userService";

/**
 * Bell icon with unread count + dropdown of recent notifications.
 * Polls every 30s.
 */
export default function NotificationBell() {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);

  const refresh = () => {
    listNotifications(false).then(setItems).catch(() => {});
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 30000);
    return () => clearInterval(t);
  }, []);

  const unread = items.filter((n) => !n.is_read).length;

  const handleMarkAll = async () => {
    await markAllRead();
    refresh();
  };

  return (
    <div className="notif-wrapper">
      <button className="notif-bell" onClick={() => setOpen((o) => !o)} aria-label="Notifications">
        <span>🔔</span>
        {unread > 0 && <span className="notif-badge">{unread}</span>}
      </button>
      {open && (
        <div className="notif-panel" onClick={(e) => e.stopPropagation()}>
          <div className="notif-header">
            <strong>Notifications</strong>
            {unread > 0 && <button className="link" onClick={handleMarkAll}>Mark all read</button>}
          </div>
          {items.length === 0 ? (
            <div className="notif-empty">No notifications</div>
          ) : (
            <ul className="notif-list">
              {items.slice(0, 10).map((n) => (
                <li key={n.notification_id} className={n.is_read ? "" : "unread"}>
                  <div className="notif-msg">{n.message}</div>
                  <div className="notif-time">{new Date(n.created_date).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
