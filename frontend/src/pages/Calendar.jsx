import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { DateTime } from 'luxon';
import { Clock, Settings, Calendar as CalendarIcon, AlertTriangle, Trash2, X } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Calendar = ({ user, setUser }) => {
  const [bookings, setBookings] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [view, setView] = useState('week'); // week or day
  const [currentDate, setCurrentDate] = useState(() => DateTime.now().setZone(user.timezone));
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showConflictsDialog, setShowConflictsDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [bookingToDelete, setBookingToDelete] = useState(null);
  const [timezones, setTimezones] = useState([]);
  const socketRef = useRef(null);

  // Booking form state
  const [title, setTitle] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [potentialConflicts, setPotentialConflicts] = useState([]);
  const [showConflictWarning, setShowConflictWarning] = useState(false);

  useEffect(() => {
    fetchBookings();
    fetchConflicts();
    fetchTimezones();

    // Polling for real-time updates every 10 seconds
    const interval = setInterval(() => {
      fetchBookings();
      fetchConflicts();
    }, 10000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const fetchBookings = async () => {
    try {
      const response = await fetch(`${API}/bookings`);
      const data = await response.json();
      setBookings(data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    }
  };

  const fetchConflicts = async () => {
    try {
      const response = await fetch(`${API}/conflicts`);
      const data = await response.json();
      setConflicts(data);
    } catch (error) {
      console.error('Error fetching conflicts:', error);
    }
  };

  const fetchTimezones = async () => {
    try {
      const response = await fetch(`${API}/timezones`);
      const data = await response.json();
      setTimezones(data.timezones);
    } catch (error) {
      console.error('Error fetching timezones:', error);
    }
  };

  const handleSlotClick = (day, hour) => {
    const date = day.toFormat('yyyy-MM-dd');
    const startTimeStr = `${hour.toString().padStart(2, '0')}:00`;
    const endHour = hour + 1;
    const endTimeStr = `${endHour.toString().padStart(2, '0')}:00`;

    setStartDate(date);
    setStartTime(startTimeStr);
    setEndTime(endTimeStr);
    setSelectedSlot({ day, hour });
    setShowBookingDialog(true);
  };

  const checkConflicts = (startUtc, endUtc) => {
    const conflicts = [];
    const startDt = DateTime.fromISO(startUtc, { zone: 'utc' });
    const endDt = DateTime.fromISO(endUtc, { zone: 'utc' });

    for (const booking of bookings) {
      const bookingStart = DateTime.fromISO(booking.start_time, { zone: 'utc' });
      const bookingEnd = DateTime.fromISO(booking.end_time, { zone: 'utc' });

      if (startDt < bookingEnd && endDt > bookingStart) {
        conflicts.push(booking);
      }
    }

    return conflicts;
  };

  const handleCreateBooking = async (forceCreate = false) => {
    if (!title.trim() || !startDate || !startTime || !endTime) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Convert to UTC
    const startLocal = DateTime.fromISO(`${startDate}T${startTime}`, { zone: user.timezone });
    const endLocal = DateTime.fromISO(`${startDate}T${endTime}`, { zone: user.timezone });

    if (endLocal <= startLocal) {
      toast.error('End time must be after start time');
      return;
    }

    const startUtc = startLocal.toUTC().toISO();
    const endUtc = endLocal.toUTC().toISO();

    // Check for conflicts
    const conflicts = checkConflicts(startUtc, endUtc);

    if (conflicts.length > 0 && !forceCreate) {
      setPotentialConflicts(conflicts);
      setShowConflictWarning(true);
      return;
    }

    try {
      const response = await fetch(`${API}/bookings?user_id=${user.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          start_time: startUtc,
          end_time: endUtc,
          notes,
          user_timezone: user.timezone,
        }),
      });

      if (response.ok) {
        toast.success(conflicts.length > 0 ? 'Booking created (conflict noted)' : 'Booking created successfully');
        setShowBookingDialog(false);
        setShowConflictWarning(false);
        resetForm();
        fetchBookings();
        fetchConflicts();
      } else {
        toast.error('Failed to create booking');
      }
    } catch (error) {
      console.error('Error creating booking:', error);
      toast.error('An error occurred');
    }
  };

  const handleDeleteBooking = async () => {
    if (!bookingToDelete) return;

    try {
      const response = await fetch(`${API}/bookings/${bookingToDelete.id}?user_id=${user.id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast.success('Booking deleted');
        setShowDeleteDialog(false);
        setBookingToDelete(null);
        fetchBookings();
        fetchConflicts();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete booking');
      }
    } catch (error) {
      console.error('Error deleting booking:', error);
      toast.error('An error occurred');
    }
  };

  const handleUpdateTimezone = async (newTimezone) => {
    try {
      const response = await fetch(`${API}/users/${user.id}/timezone?timezone=${encodeURIComponent(newTimezone)}`, {
        method: 'PUT',
      });

      if (response.ok) {
        setUser({ ...user, timezone: newTimezone });
        setCurrentDate(DateTime.now().setZone(newTimezone));
        toast.success('Timezone updated');
        setShowSettingsDialog(false);
      } else {
        toast.error('Failed to update timezone');
      }
    } catch (error) {
      console.error('Error updating timezone:', error);
      toast.error('An error occurred');
    }
  };

  const resetForm = () => {
    setTitle('');
    setStartDate('');
    setStartTime('');
    setEndTime('');
    setNotes('');
    setSelectedSlot(null);
    setPotentialConflicts([]);
  };

  const getWeekDays = () => {
    if (!currentDate || !currentDate.isValid) {
      const now = DateTime.now().setZone(user.timezone);
      const startOfWeek = now.startOf('week');
      const days = [];
      for (let i = 0; i < 7; i++) {
        days.push(startOfWeek.plus({ days: i }));
      }
      return days;
    }
    
    const startOfWeek = currentDate.startOf('week');
    const days = [];
    for (let i = 0; i < 7; i++) {
      days.push(startOfWeek.plus({ days: i }));
    }
    return days;
  };

  const getHours = () => {
    return Array.from({ length: 24 }, (_, i) => i);
  };

  const getBookingsForSlot = (day, hour) => {
    const slotStart = day.set({ hour, minute: 0, second: 0, millisecond: 0 });
    const slotEnd = slotStart.plus({ hours: 1 });

    return bookings.filter((booking) => {
      const bookingStart = DateTime.fromISO(booking.start_time, { zone: 'utc' }).setZone(user.timezone);
      const bookingEnd = DateTime.fromISO(booking.end_time, { zone: 'utc' }).setZone(user.timezone);

      return bookingStart < slotEnd && bookingEnd > slotStart;
    });
  };

  const hasConflict = (booking) => {
    return conflicts.some(
      (conflict) =>
        conflict.booking1_id === booking.id || conflict.booking2_id === booking.id
    );
  };

  const getUserConflicts = () => {
    return conflicts.filter(
      (conflict) => conflict.user1_id === user.id || conflict.user2_id === user.id
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-[#0f0f0f]">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>notcluely</h1>
            <p className="text-sm text-gray-400">Welcome, {user.name} {user.is_admin && <span className="text-cyan-500">(Admin)</span>}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                <span>{user.timezone}</span>
              </div>
            </div>
            
            {(getUserConflicts().length > 0 || (user.is_admin && conflicts.length > 0)) && (
              <Button
                data-testid="conflicts-button"
                onClick={() => setShowConflictsDialog(true)}
                variant="outline"
                className="border-red-500 text-red-500 hover:bg-red-500 hover:text-white relative"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Conflicts
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {user.is_admin ? conflicts.length : getUserConflicts().length}
                </span>
              </Button>
            )}
            
            <Button
              data-testid="settings-button"
              onClick={() => setShowSettingsDialog(true)}
              variant="ghost"
              className="text-gray-400 hover:text-white"
            >
              <Settings className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Calendar Controls */}
      <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            onClick={() => setCurrentDate(currentDate.minus({ weeks: 1 }))}
            variant="outline"
            className="border-gray-700 text-white hover:bg-gray-800"
          >
            Previous
          </Button>
          <Button
            onClick={() => setCurrentDate(DateTime.now().setZone(user.timezone))}
            variant="outline"
            className="border-gray-700 text-white hover:bg-gray-800"
          >
            Today
          </Button>
          <Button
            onClick={() => setCurrentDate(currentDate.plus({ weeks: 1 }))}
            variant="outline"
            className="border-gray-700 text-white hover:bg-gray-800"
          >
            Next
          </Button>
          <span className="text-lg font-medium ml-4">
            {currentDate.toFormat('MMMM yyyy')}
          </span>
        </div>

        <Button
          data-testid="create-booking-button"
          onClick={() => {
            resetForm();
            setShowBookingDialog(true);
          }}
          className="bg-cyan-600 hover:bg-cyan-700 text-white"
        >
          <CalendarIcon className="w-4 h-4 mr-2" />
          New Booking
        </Button>
      </div>

      {/* Calendar Grid */}
      <div className="max-w-[1600px] mx-auto px-6 pb-8">
        <div className="bg-[#0f0f0f] border border-gray-800 rounded-lg overflow-hidden">
          {/* Week Header */}
          <div className="grid grid-cols-8 border-b border-gray-800">
            <div className="p-3 border-r border-gray-800 bg-[#151515] text-sm text-gray-500">Time</div>
            {getWeekDays().map((day, idx) => {
              const isToday = day.hasSame(DateTime.now().setZone(user.timezone), 'day');
              return (
                <div
                  key={`header-day-${idx}`}
                  className="p-3 border-r border-gray-800 bg-[#151515] text-center"
                >
                  <div className="text-sm text-gray-400">{day.toFormat('EEE')}</div>
                  <div className={`text-lg font-semibold ${isToday ? 'text-cyan-500' : 'text-white'}`}>
                    {day.toFormat('d')}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Time Slots */}
          <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 300px)' }}>
            {getHours().map((hour) => {
              const weekDays = getWeekDays();
              return (
                <div key={`hour-${hour}`} className="grid grid-cols-8 border-b border-gray-800 hover:bg-[#151515]">
                  <div className="p-3 border-r border-gray-800 text-sm text-gray-500 flex items-start">
                    {DateTime.fromObject({ hour }).toFormat('ha')}
                  </div>
                  {weekDays.map((day, dayIdx) => {
                    const slotBookings = getBookingsForSlot(day, hour);
                    return (
                      <div
                        key={`slot-${hour}-${dayIdx}`}
                        data-testid={`time-slot-${day.toFormat('yyyy-MM-dd')}-${hour}`}
                        onClick={() => slotBookings.length === 0 && handleSlotClick(day, hour)}
                        className={`p-2 border-r border-gray-800 min-h-[60px] relative ${
                          slotBookings.length === 0 ? 'cursor-pointer hover:bg-[#1a1a1a]' : ''
                        }`}
                      >
                        {slotBookings.map((booking, idx) => {
                          const isConflict = hasConflict(booking);
                          const isOwner = booking.user_id === user.id;
                          return (
                            <div
                              key={`booking-${booking.id}-${idx}`}
                              data-testid={`booking-${booking.id}`}
                              className={`text-xs p-2 rounded mb-1 ${
                                isConflict
                                  ? 'bg-red-900/50 border border-red-500'
                                  : 'bg-cyan-900/30 border border-cyan-700'
                              } ${isOwner ? 'font-semibold' : ''}`}
                              style={{ zIndex: 10 + idx }}
                            >
                              <div className="flex items-start justify-between gap-1">
                                <div className="flex-1 min-w-0">
                                  <div className="truncate font-medium">{booking.title}</div>
                                  <div className="text-gray-400 truncate">{booking.user_name}</div>
                                </div>
                                {(isOwner || user.is_admin) && (
                                  <button
                                    data-testid={`delete-booking-${booking.id}`}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setBookingToDelete(booking);
                                      setShowDeleteDialog(true);
                                    }}
                                    className="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                              {isConflict && (
                                <div className="flex items-center gap-1 mt-1 text-red-400">
                                  <AlertTriangle className="w-3 h-3" />
                                  <span className="text-[10px]">Conflict</span>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              );
            })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Create Booking Dialog */}
      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent className="bg-[#151515] border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>Create Booking</DialogTitle>
            <DialogDescription className="text-gray-400">
              Book a time slot in your timezone ({user.timezone})
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div>
              <Label htmlFor="title" className="text-gray-300">Meeting Title</Label>
              <Input
                id="title"
                data-testid="booking-title-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Client Meeting"
                className="bg-[#0a0a0a] border-gray-700 text-white mt-1"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start-date" className="text-gray-300">Date</Label>
                <Input
                  id="start-date"
                  data-testid="booking-date-input"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-[#0a0a0a] border-gray-700 text-white mt-1"
                />
              </div>
              <div></div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start-time" className="text-gray-300">Start Time</Label>
                <Input
                  id="start-time"
                  data-testid="booking-start-time-input"
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="bg-[#0a0a0a] border-gray-700 text-white mt-1"
                />
              </div>
              <div>
                <Label htmlFor="end-time" className="text-gray-300">End Time</Label>
                <Input
                  id="end-time"
                  data-testid="booking-end-time-input"
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="bg-[#0a0a0a] border-gray-700 text-white mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="notes" className="text-gray-300">Notes (Optional)</Label>
              <Textarea
                id="notes"
                data-testid="booking-notes-input"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional details"
                className="bg-[#0a0a0a] border-gray-700 text-white mt-1"
                rows={3}
              />
            </div>

            <Button
              data-testid="submit-booking-button"
              onClick={() => handleCreateBooking(false)}
              className="w-full bg-cyan-600 hover:bg-cyan-700"
            >
              Create Booking
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Conflict Warning Dialog */}
      <AlertDialog open={showConflictWarning} onOpenChange={setShowConflictWarning}>
        <AlertDialogContent className="bg-[#151515] border-gray-800 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-500">
              <AlertTriangle className="w-5 h-5" />
              Booking Conflict Detected
            </AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              This time slot is already booked by:
              <ul className="mt-2 space-y-1">
                {potentialConflicts.map((conflict) => {
                  const startLocal = DateTime.fromISO(conflict.start_time, { zone: 'utc' }).setZone(user.timezone);
                  const endLocal = DateTime.fromISO(conflict.end_time, { zone: 'utc' }).setZone(user.timezone);
                  return (
                    <li key={conflict.id} className="text-white">
                      <strong>{conflict.user_name}</strong> - {conflict.title}
                      <br />
                      <span className="text-sm text-gray-500">
                        {startLocal.toFormat('h:mm a')} - {endLocal.toFormat('h:mm a')} ({user.timezone})
                      </span>
                    </li>
                  );
                })}
              </ul>
              <p className="mt-3 text-yellow-500">Continue to create a conflicting booking? Both users will be notified.</p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-[#0a0a0a] border-gray-700 text-white hover:bg-gray-800">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              data-testid="confirm-conflict-button"
              onClick={() => handleCreateBooking(true)}
              className="bg-red-600 hover:bg-red-700"
            >
              Create Anyway
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Booking Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="bg-[#151515] border-gray-800 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Booking?</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              Are you sure you want to delete &quot;{bookingToDelete?.title}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-[#0a0a0a] border-gray-700 text-white hover:bg-gray-800">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteBooking}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="bg-[#151515] border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle>Settings</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-gray-300">Name</Label>
              <Input
                value={user.name}
                disabled
                className="bg-[#0a0a0a] border-gray-700 text-gray-500 mt-1"
              />
            </div>

            <div>
              <Label htmlFor="timezone-setting" className="text-gray-300">Timezone</Label>
              <Select defaultValue={user.timezone} onValueChange={handleUpdateTimezone}>
                <SelectTrigger id="timezone-setting" className="bg-[#0a0a0a] border-gray-700 text-white mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#151515] border-gray-700 text-white max-h-[300px]">
                  {timezones.map((tz) => (
                    <SelectItem key={tz} value={tz} className="text-white hover:bg-[#0a0a0a] focus:bg-[#0a0a0a]">
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Conflicts Dialog */}
      <Dialog open={showConflictsDialog} onOpenChange={setShowConflictsDialog}>
        <DialogContent className="bg-[#151515] border-gray-800 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Active Conflicts
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              {user.is_admin ? 'All system conflicts' : 'Your booking conflicts'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 mt-4 max-h-[400px] overflow-y-auto">
            {(user.is_admin ? conflicts : getUserConflicts()).length === 0 ? (
              <p className="text-gray-500 text-center py-8">No active conflicts</p>
            ) : (
              (user.is_admin ? conflicts : userConflicts).map((conflict) => {
                const startLocal = DateTime.fromISO(conflict.conflict_start, { zone: 'utc' }).setZone(user.timezone);
                const endLocal = DateTime.fromISO(conflict.conflict_end, { zone: 'utc' }).setZone(user.timezone);
                
                return (
                  <div key={conflict.id} className="bg-[#0a0a0a] border border-red-500/50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-red-400 mb-2">Double Booking Detected</div>
                        <div className="text-sm space-y-1">
                          <div><strong>{conflict.user1_name}</strong> and <strong>{conflict.user2_name}</strong></div>
                          <div className="text-gray-400">
                            {startLocal.toFormat('MMM d, yyyy')} • {startLocal.toFormat('h:mm a')} - {endLocal.toFormat('h:mm a')}
                          </div>
                          <div className="text-gray-500 text-xs">Your timezone: {user.timezone}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Calendar;