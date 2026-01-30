import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { DateTime } from 'luxon';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = ({ fingerprint, setUser }) => {
  const [name, setName] = useState('');
  const [timezone, setTimezone] = useState(() => {
    // Initialize with detected timezone immediately
    try {
      return DateTime.local().zoneName || 'UTC';
    } catch {
      return 'UTC';
    }
  });
  const [timezones, setTimezones] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Auto-detect timezone and ensure it's set
    try {
      const detectedTimezone = DateTime.local().zoneName || 'UTC';
      setTimezone(detectedTimezone);
    } catch (error) {
      console.error('Error detecting timezone:', error);
      setTimezone('UTC');
    }

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
        // Fallback to common timezones if fetch fails
        setTimezones(['UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo']);
      }
    };

    fetchTimezones();
  }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!name.trim()) {
      toast.error('Please enter your name');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API}/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          fingerprint,
          timezone,
        }),
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        toast.success(userData.is_admin ? 'Welcome Admin!' : 'Registration successful!');
      } else {
        toast.error('Registration failed');
      }
    } catch (error) {
      console.error('Error registering:', error);
      toast.error('An error occurred');
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
          <h2 className="text-2xl font-semibold text-white mb-6">Get Started</h2>
          
          <form onSubmit={handleRegister} className="space-y-6">
            <div>
              <Label htmlFor="name" className="text-gray-300 mb-2 block">Your Name</Label>
              <Input
                id="name"
                data-testid="name-input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="bg-[#0a0a0a] border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500 focus:ring-cyan-500"
              />
            </div>

            <div>
              <Label htmlFor="timezone" className="text-gray-300 mb-2 block">Your Timezone</Label>
              <Select value={timezone} onValueChange={setTimezone}>
                <SelectTrigger data-testid="timezone-select" className="bg-[#0a0a0a] border-gray-700 text-white focus:border-cyan-500 focus:ring-cyan-500">
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent className="bg-[#151515] border-gray-700 text-white max-h-[300px]">
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
              data-testid="register-button"
              type="submit"
              disabled={loading}
              className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-medium py-6 rounded-lg transition-colors"
            >
              {loading ? 'Registering...' : 'Continue'}
            </Button>
          </form>
        </div>

        <p className="text-center text-gray-500 text-xs mt-6">
          Your browser fingerprint ensures automatic login on return visits
        </p>
      </div>
    </div>
  );
};

export default Home;