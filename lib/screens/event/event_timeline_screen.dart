import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';
import '../../services/auth_service.dart';
import '../../services/event_service.dart';
import 'deep_dive_screen.dart';

class EventTimelineScreen extends StatelessWidget {
  final int eventId;
  final Map<String, dynamic> eventData;

  EventTimelineScreen({required this.eventId, required this.eventData});

  @override
  Widget build(BuildContext context) {
    final timeline = eventData['timeline'] as List<dynamic>;
    final vendors = eventData['vendors'] as List<dynamic>? ?? [];
    final eventDetails = eventData['event_details'] as Map<String, dynamic>;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: CustomScrollView(
        slivers: [
          // App Bar
          SliverAppBar(
            expandedHeight: 200,
            floating: false,
            pinned: true,
            backgroundColor: Colors.purple,
            foregroundColor: Colors.white,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                '${eventDetails['event_type'].toString().toUpperCase()} TIMELINE',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.purple[400]!, Colors.purple[600]!],
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      SizedBox(height: 40), // Space for status bar
                      Icon(Icons.auto_awesome, size: 48, color: Colors.white),
                      SizedBox(height: 8),
                      Text(
                        'AI Generated Plan',
                        style: TextStyle(color: Colors.white70, fontSize: 16),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Content
          SliverToBoxAdapter(
            child: Column(
              children: [
                // Event Summary
                Container(
                  margin: EdgeInsets.all(16),
                  padding: EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 8,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.info_outline, color: Colors.purple),
                          SizedBox(width: 8),
                          Text(
                            'Event Summary',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.purple,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 16),
                      _buildSummaryRow(
                        Icons.location_on,
                        'Location',
                        eventDetails['location'],
                      ),
                      _buildSummaryRow(
                        Icons.calendar_today,
                        'Duration',
                        '${timeline.length} day${timeline.length > 1 ? 's' : ''}',
                      ),
                      _buildSummaryRow(
                        Icons.currency_rupee,
                        'Budget',
                        eventData['estimated_budget'] != null
                            ? '₹${eventData['estimated_budget'].toStringAsFixed(0)}'
                            : 'Not specified',
                      ),
                      if (eventDetails['religion'] != null)
                        _buildSummaryRow(
                          Icons.account_balance,
                          'Religion',
                          eventDetails['religion'].toString().toUpperCase(),
                        ),
                    ],
                  ),
                ),

                // Timeline Section
                Container(
                  margin: EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      Icon(Icons.timeline, color: Colors.purple),
                      SizedBox(width: 8),
                      Text(
                        'Event Timeline',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[800],
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(height: 12),

                // Timeline Cards
                ...timeline.asMap().entries.map((entry) {
                  final index = entry.key;
                  final day = entry.value;
                  return TimelineDayCard(
                    eventId: eventId,
                    dayData: day,
                    isLast: index == timeline.length - 1,
                  );
                }).toList(),

                SizedBox(height: 24),

                // Vendors Section
                if (vendors.isNotEmpty) ...[
                  Container(
                    margin: EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      children: [
                        Icon(Icons.business, color: Colors.purple),
                        SizedBox(width: 8),
                        Text(
                          'Recommended Vendors',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.grey[800],
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(height: 12),
                  ...vendors
                      .map((vendor) => VendorCard(vendor: vendor))
                      .toList(),
                  SizedBox(height: 24),
                ],

                // Bottom padding
                SizedBox(height: 80),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(IconData icon, String label, String value) {
    return Padding(
      padding: EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.grey[600]),
          SizedBox(width: 12),
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(value, style: TextStyle(color: Colors.grey[800])),
          ),
        ],
      ),
    );
  }
}

class TimelineDayCard extends StatelessWidget {
  final int eventId;
  final Map<String, dynamic> dayData;
  final bool isLast;

  TimelineDayCard({
    required this.eventId,
    required this.dayData,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final details = dayData['details'] as List<dynamic>? ?? [];

    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline indicator
          Column(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: Colors.purple,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    '${dayData['day']}',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
              if (!isLast)
                Container(
                  width: 2,
                  height: 100,
                  color: Colors.purple.withOpacity(0.3),
                ),
            ],
          ),

          SizedBox(width: 16),

          // Content card
          Expanded(
            child: Container(
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 8,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Day header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Day ${dayData['day']}',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.purple,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              dayData['date'] ?? '',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (dayData['estimated_cost'] != null)
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.green.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            '₹${dayData['estimated_cost'].toStringAsFixed(0)}',
                            style: TextStyle(
                              color: Colors.green[700],
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                    ],
                  ),

                  SizedBox(height: 12),

                  // Summary
                  Text(
                    dayData['summary'] ?? '',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: Colors.grey[800],
                    ),
                  ),

                  SizedBox(height: 16),

                  // Details
                  ...details
                      .take(3)
                      .map<Widget>(
                        (detail) => Padding(
                          padding: EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                margin: EdgeInsets.only(top: 6, right: 12),
                                decoration: BoxDecoration(
                                  color: Colors.purple.withOpacity(0.6),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  detail.toString(),
                                  style: TextStyle(
                                    color: Colors.grey[700],
                                    height: 1.4,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      )
                      .toList(),

                  if (details.length > 3)
                    Text(
                      '+${details.length - 3} more activities',
                      style: TextStyle(
                        color: Colors.purple,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),

                  SizedBox(height: 16),

                  // Deep dive button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () => _showDeepDive(context, dayData['day']),
                      icon: Icon(Icons.schedule, size: 18),
                      label: Text('View Detailed Schedule'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.purple.withOpacity(0.1),
                        foregroundColor: Colors.purple,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showDeepDive(BuildContext context, int dayNumber) async {
    // Show loading dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder:
          (context) => AlertDialog(
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(color: Colors.purple),
                SizedBox(height: 16),
                Text('Generating detailed schedule...'),
              ],
            ),
          ),
    );

    try {
      final authService = Provider.of<AuthService>(context, listen: false);
      final eventService = Provider.of<EventService>(context, listen: false);

      final deepDive = await eventService.getDeepDive(
        authService,
        eventId,
        dayNumber,
      );

      Navigator.of(context).pop(); // Close loading dialog

      if (deepDive != null) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => DeepDiveScreen(deepDiveData: deepDive),
          ),
        );
      } else {
        _showError(context, 'Failed to load detailed schedule');
      }
    } catch (e) {
      Navigator.of(context).pop(); // Close loading dialog
      _showError(context, 'Error: $e');
    }
  }

  void _showError(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }
}

class VendorCard extends StatelessWidget {
  final Map<String, dynamic> vendor;

  VendorCard({required this.vendor});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: ListTile(
          contentPadding: EdgeInsets.all(16),
          title: Text(
            vendor['title'] ?? 'Vendor',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: Colors.grey[800],
            ),
          ),
          subtitle:
              vendor['snippet'] != null
                  ? Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: Text(
                      vendor['snippet'],
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(color: Colors.grey[600], height: 1.4),
                    ),
                  )
                  : null,
          trailing:
              vendor['url'] != null
                  ? IconButton(
                    icon: Icon(Icons.open_in_new, color: Colors.purple),
                    onPressed: () => _launchUrl(vendor['url']),
                  )
                  : null,
          onTap: vendor['url'] != null ? () => _launchUrl(vendor['url']) : null,
        ),
      ),
    );
  }

  void _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
