import React, { useEffect, useState } from "react";
import { listUsers, createUser, updateUser, deleteUser } from "../services/userService";
import Modal from "../components/Modal";
import Toast from "../components/Toast";

const ROLES = ["Admin", "Supervisor", "Support Agent", "Customer"];

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [editing, setEditing] = useState(null); // null | {} | user
  const [toast, setToast] = useState({ message: "" });

  const refresh = () => listUsers().then(setUsers);
  useEffect(() => { refresh(); }, []);

  const handleSave = async (form) => {
    try {
      if (editing && editing.user_id) {
        await updateUser(editing.user_id, {
          name: form.name, phone: form.phone, is_active: form.is_active, role_name: form.role_name,
        });
        setToast({ message: "User updated", type: "success" });
      } else {
        await createUser({
          name: form.name, email: form.email, password: form.password,
          phone: form.phone, role_name: form.role_name,
        });
        setToast({ message: "User created", type: "success" });
      }
      setEditing(null);
      refresh();
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Save failed", type: "error" });
    }
  };

  const handleDelete = async (u) => {
    if (!window.confirm(`Delete ${u.name}?`)) return;
    try {
      await deleteUser(u.user_id);
      setToast({ message: "User deleted", type: "success" });
      refresh();
    } catch (e) {
      setToast({ message: e?.response?.data?.detail || "Delete failed", type: "error" });
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">Admin controls for users and roles</p>
        </div>
        <button className="btn btn-primary" onClick={() => setEditing({})}>+ Add User</button>
      </div>

      <table className="data-table">
        <thead>
          <tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Phone</th><th>Active</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.user_id}>
              <td>{u.user_id}</td>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td><span className={`role-tag role-${u.role_name.replace(/\s/g, "-").toLowerCase()}`}>{u.role_name}</span></td>
              <td>{u.phone || "—"}</td>
              <td>{u.is_active ? <span className="badge badge-green">Active</span> : <span className="badge badge-red">Disabled</span>}</td>
              <td>
                <button className="btn btn-sm" onClick={() => setEditing(u)}>Edit</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal open={editing !== null} title={editing?.user_id ? "Edit User" : "Add User"} onClose={() => setEditing(null)}>
        {editing !== null && <UserForm initial={editing} onSubmit={handleSave} onCancel={() => setEditing(null)} />}
      </Modal>

      <Toast {...toast} onClose={() => setToast({ message: "" })} />
    </div>
  );
}

function UserForm({ initial, onSubmit, onCancel }) {
  const editing = !!initial.user_id;
  const [f, setF] = useState({
    name: initial.name || "",
    email: initial.email || "",
    password: "",
    phone: initial.phone || "",
    role_name: initial.role_name || "Customer",
    is_active: initial.is_active !== false,
  });

  const submit = (e) => {
    e.preventDefault();
    onSubmit(f);
  };

  return (
    <form className="form" onSubmit={submit}>
      <div className="form-group">
        <label>Name</label>
        <input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required />
      </div>
      {!editing && (
        <>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required minLength={6} />
          </div>
        </>
      )}
      <div className="form-group">
        <label>Phone</label>
        <input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />
      </div>
      <div className="form-group">
        <label>Role</label>
        <select value={f.role_name} onChange={(e) => setF({ ...f, role_name: e.target.value })}>
          {ROLES.map((r) => <option key={r}>{r}</option>)}
        </select>
      </div>
      {editing && (
        <div className="form-group">
          <label>
            <input type="checkbox" checked={f.is_active} onChange={(e) => setF({ ...f, is_active: e.target.checked })} />
            {" "}Active
          </label>
        </div>
      )}
      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary">Save</button>
      </div>
    </form>
  );
}
