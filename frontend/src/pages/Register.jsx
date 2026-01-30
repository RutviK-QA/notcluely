import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { DateTime } from 'luxon';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = ({ onRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [timezone, setTimezone] = useState(() => {
    try {
      return DateTime.local().zoneName || 'UTC';
    } catch {
      return 'UTC';
    }
  });
  const [timezones, setTimezones] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch available timezones
    const fetchTimezones = async () => {
      try {
        const response = await fetch(`${API}/timezones`);
        if (response.ok) {
          const data = await response.json();
          setTimezones(data.timezones);
        }
      } catch (error) {
        console.error('Error fetching timezones:', error);
        setTimezones(['UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo']);
      }
    };

    fetchTimezones();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!username.trim()) {
      toast.error('Please enter a username');
      return;
    }

    if (username.trim().length < 3) {
      toast.error('Username must be at least 3 characters');
      return;
    }

    if (!password) {
      toast.error('Please enter a password');
      return;
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (!timezone) {
      toast.error('Please select a timezone');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
          timezone,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(data.user.is_admin ? 'Welcome, Admin!' : 'Registration successful!');
        onRegister(data.access_token, data.user);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>notcluely</h1>
          <p className="text-gray-400 text-sm">Shared Profile Scheduler</p>
        </div>

        <div className="bg-[#151515] border border-gray-800 rounded-lg p-8 shadow-2xl">
          <h2 className="text-2xl font-semibold text-white mb-6">Register</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="username" className="text-gray-300 mb-2 block">Username</Label>
              <Input
                id="username"
                data-testid="register-username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username (min 3 chars)"
                className="bg-[#0a0a0a] border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500 focus:ring-cyan-500"
                autoComplete="username"
              />
              <p className="text-xs text-gray-500 mt-1">Enter 'rutvik' for admin access</p>
            </div>

            <div>
              <Label htmlFor="password" className="text-gray-300 mb-2 block">Password</Label>
              <Input
                id="password"
                data-testid="register-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Choose a password (min 8 chars)"
                className="bg-[#0a0a0a] border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500 focus:ring-cyan-500"
                autoComplete="new-password"
              />
            </div>

            <div>
              <Label htmlFor="confirm-password" className="text-gray-300 mb-2 block">Confirm Password</Label>
              <Input
                id="confirm-password"
                data-testid="register-confirm-password-input"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                className="bg-[#0a0a0a] border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500 focus:ring-cyan-500"
                autoComplete="new-password"
              />
            </div>

            <div>
              <Label htmlFor="timezone" className="text-gray-300 mb-2 block">Timezone</Label>
              <Select value={timezone} onValueChange={setTimezone}>
                <SelectTrigger data-testid="register-timezone-select" className="bg-[#0a0a0a] border-gray-700 text-white focus:border-cyan-500 focus:ring-cyan-500">
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent className="bg-[#151515] border-gray-700 text-white max-h-[300px] z-[1002]">
                  {timezones.map((tz) => (
                    <SelectItem key={tz} value={tz} className="text-white hover:bg-[#0a0a0a] focus:bg-[#0a0a0a]">
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">Auto-detected: {DateTime.local().zoneName}</p>
            </div>

            <Button
              data-testid="register-submit-button"
              type="submit"
              disabled={loading}
              className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-medium py-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating account...' : 'Register'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-400 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-cyan-500 hover:text-cyan-400 font-medium">
                Login here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;