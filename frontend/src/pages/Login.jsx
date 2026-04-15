import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api.js';
import { saveAuth } from '../auth.js';

export default function LoginPage({ onLogin, selectedRole, setSelectedRole }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const data = await login({ username, password });

      if (data.user.role !== selectedRole) {
        setError(`Access denied. You are not recorded as a ${selectedRole}.`);
        return;
      }

      saveAuth(data);
      onLogin(data.user);

      if (data.user.role === 'owner') {
        navigate('/owner');
      } else if (data.user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Unable to login.');
    }
  };

  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Welcome back</h1>
        <p>Use your credentials to access the support dashboard.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>

        <div className="role-selector">
          <label className="radio-label">
            <input type="radio" value="admin" checked={selectedRole === 'admin'} onChange={() => setSelectedRole('admin')} />
            Admin
          </label>
          <label className="radio-label">
            <input type="radio" value="owner" checked={selectedRole === 'owner'} onChange={() => setSelectedRole('owner')} />
            Owner
          </label>
        </div>

        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>

        {error && <div className="form-error">{error}</div>}

        <button className="button button-primary" type="submit">
          Login
        </button>
      </form>
    </section>
  );
}
