import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../services/auth_service.dart';
import '../../services/event_service.dart';
import 'event_timeline_screen.dart';

class CreateEventScreen extends StatefulWidget {
  @override
  _CreateEventScreenState createState() => _CreateEventScreenState();
}

class _CreateEventScreenState extends State<CreateEventScreen> {
  final _formKey = GlobalKey<FormState>();
  final _locationController = TextEditingController();
  final _budgetController = TextEditingController();

  String _eventType = 'wedding';
  DateTime _startDate = DateTime.now().add(Duration(days: 30));
  DateTime? _endDate;
  TimeOfDay _startTime = TimeOfDay(hour: 10, minute: 0); // Default 10:00 AM
  String? _religion;
  bool _isMultiDay = false;

  final List<String> _eventTypes = [
    'wedding',
    'birthday',
    'anniversary',
    'housewarming',
    'corporate',
    'graduation',
    'baby_shower',
    'engagement',
    'festival',
    'conference',
  ];

  final List<String> _religions = [
    'hindu',
    'muslim',
    'christian',
    'sikh',
    'buddhist',
    'jain',
    'jewish',
    'secular',
    'mixed',
  ];

  @override
  void initState() {
    super.initState();
    // Set default end date for wedding
    if (_eventType == 'wedding') {
      _endDate = _startDate.add(Duration(days: 2));
      _isMultiDay = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text('Create Event'),
        backgroundColor: Colors.purple,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.purple,
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(32),
                  bottomRight: Radius.circular(32),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Plan Your Event',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'AI will create a customized timeline for you',
                    style: TextStyle(color: Colors.white70, fontSize: 16),
                  ),
                ],
              ),
            ),

            // Form
            Padding(
              padding: EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Event Type
                    Text(
                      'Event Type',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: _eventType,
                      decoration: InputDecoration(
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        prefixIcon: Icon(Icons.event),
                      ),
                      items:
                          _eventTypes
                              .map(
                                (type) => DropdownMenuItem(
                                  value: type,
                                  child: Text(type.toUpperCase()),
                                ),
                              )
                              .toList(),
                      onChanged: (value) {
                        setState(() {
                          _eventType = value!;
                          // Auto-set multi-day for wedding
                          if (_eventType == 'wedding') {
                            _isMultiDay = true;
                            _endDate = _startDate.add(Duration(days: 2));
                          } else {
                            _isMultiDay = false;
                            _endDate = null;
                          }
                        });
                      },
                    ),
                    SizedBox(height: 24),

                    // Location
                    Text(
                      'Location',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    TextFormField(
                      controller: _locationController,
                      decoration: InputDecoration(
                        hintText: 'e.g., Mumbai, India',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        prefixIcon: Icon(Icons.location_on),
                      ),
                      validator: (value) {
                        if (value?.isEmpty ?? true)
                          return 'Location is required';
                        return null;
                      },
                    ),
                    SizedBox(height: 24),

                    // Start Date
                    Text(
                      'Start Date',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    InkWell(
                      onTap: _selectStartDate,
                      child: Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.calendar_today, color: Colors.grey[600]),
                            SizedBox(width: 12),
                            Text(
                              DateFormat('MMM dd, yyyy').format(_startDate),
                              style: TextStyle(fontSize: 16),
                            ),
                          ],
                        ),
                      ),
                    ),
                    SizedBox(height: 16),

                    // Start Time
                    Text(
                      'Start Time',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    InkWell(
                      onTap: _selectStartTime,
                      child: Container(
                        width: double.infinity,
                        padding: EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.grey),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.access_time, color: Colors.grey[600]),
                            SizedBox(width: 12),
                            Text(
                              _startTime.format(context),
                              style: TextStyle(fontSize: 16),
                            ),
                          ],
                        ),
                      ),
                    ),
                    SizedBox(height: 16),

                    // Multi-day toggle
                    if (_eventType != 'wedding') ...[
                      Row(
                        children: [
                          Switch(
                            value: _isMultiDay,
                            onChanged: (value) {
                              setState(() {
                                _isMultiDay = value;
                                if (!_isMultiDay) {
                                  _endDate = null;
                                } else {
                                  _endDate = _startDate.add(Duration(days: 1));
                                }
                              });
                            },
                            activeColor: Colors.purple,
                          ),
                          Text(
                            'Multi-day event',
                            style: TextStyle(fontSize: 16),
                          ),
                        ],
                      ),
                      SizedBox(height: 16),
                    ],

                    // End Date (if multi-day)
                    if (_isMultiDay) ...[
                      Text(
                        'End Date',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[800],
                        ),
                      ),
                      SizedBox(height: 8),
                      InkWell(
                        onTap: _selectEndDate,
                        child: Container(
                          width: double.infinity,
                          padding: EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.calendar_today,
                                color: Colors.grey[600],
                              ),
                              SizedBox(width: 12),
                              Text(
                                _endDate != null
                                    ? DateFormat(
                                      'MMM dd, yyyy',
                                    ).format(_endDate!)
                                    : 'Select end date',
                                style: TextStyle(
                                  fontSize: 16,
                                  color:
                                      _endDate != null
                                          ? Colors.black
                                          : Colors.grey,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      SizedBox(height: 24),
                    ],

                    // Budget (Optional)
                    Text(
                      'Budget (Optional)',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    TextFormField(
                      controller: _budgetController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        hintText: 'Enter total budget',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        prefixIcon: Icon(Icons.currency_rupee),
                      ),
                    ),
                    SizedBox(height: 24),

                    // Religion (Optional)
                    Text(
                      'Religion (Optional)',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: _religion,
                      decoration: InputDecoration(
                        hintText: 'Select religion (optional)',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        prefixIcon: Icon(Icons.account_balance),
                      ),
                      items: [
                        DropdownMenuItem(
                          value: null,
                          child: Text('Not specified'),
                        ),
                        ..._religions
                            .map(
                              (religion) => DropdownMenuItem(
                                value: religion,
                                child: Text(religion.toUpperCase()),
                              ),
                            )
                            .toList(),
                      ],
                      onChanged: (value) {
                        setState(() {
                          _religion = value;
                        });
                      },
                    ),
                    SizedBox(height: 32),

                    // Create Event Button
                    Consumer2<AuthService, EventService>(
                      builder: (context, authService, eventService, child) {
                        return SizedBox(
                          width: double.infinity,
                          height: 56,
                          child: ElevatedButton(
                            onPressed:
                                eventService.isLoading ? null : _createEvent,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.purple,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                              elevation: 4,
                            ),
                            child:
                                eventService.isLoading
                                    ? Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        SizedBox(
                                          width: 20,
                                          height: 20,
                                          child: CircularProgressIndicator(
                                            color: Colors.white,
                                            strokeWidth: 2,
                                          ),
                                        ),
                                        SizedBox(width: 12),
                                        Text('Creating your event...'),
                                      ],
                                    )
                                    : Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.auto_awesome, size: 24),
                                        SizedBox(width: 8),
                                        Text(
                                          'Create AI Timeline',
                                          style: TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _selectStartDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _startDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(Duration(days: 365 * 2)),
    );

    if (date != null) {
      setState(() {
        _startDate = date;
        // Adjust end date if it's before start date
        if (_endDate != null && _endDate!.isBefore(_startDate)) {
          _endDate = _startDate.add(Duration(days: 1));
        }
      });
    }
  }

  void _selectEndDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _endDate ?? _startDate.add(Duration(days: 1)),
      firstDate: _startDate,
      lastDate: DateTime.now().add(Duration(days: 365 * 2)),
    );

    if (date != null) {
      setState(() {
        _endDate = date;
      });
    }
  }

  void _selectStartTime() async {
    final time = await showTimePicker(
      context: context,
      initialTime: _startTime,
    );

    if (time != null) {
      setState(() {
        _startTime = time;
      });
    }
  }

  void _createEvent() async {
    if (_formKey.currentState!.validate()) {
      if (_isMultiDay && _endDate == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Please select an end date for multi-day event'),
            backgroundColor: Colors.orange,
          ),
        );
        return;
      }

      final authService = Provider.of<AuthService>(context, listen: false);
      final eventService = Provider.of<EventService>(context, listen: false);

      final budget =
          _budgetController.text.isNotEmpty
              ? double.tryParse(_budgetController.text)
              : null;

      // Combine date and time
      final startDateTime = DateTime(
        _startDate.year,
        _startDate.month,
        _startDate.day,
        _startTime.hour,
        _startTime.minute,
      );

      final result = await eventService.createEvent(
        authService: authService,
        eventType: _eventType,
        startDate: _startDate.toIso8601String().split('T')[0],
        startTime: _startTime.format(context),
        endDate: _endDate?.toIso8601String().split('T')[0],
        location: _locationController.text.trim(),
        budget: budget,
        religion: _religion,
      );

      if (result != null) {
        // Navigate to timeline screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder:
                (context) => EventTimelineScreen(
                  eventId: result['event_id'],
                  eventData: result,
                ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to create event. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _locationController.dispose();
    _budgetController.dispose();
    super.dispose();
  }
}
