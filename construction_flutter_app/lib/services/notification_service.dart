import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const AndroidInitializationSettings androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const InitializationSettings settings = InitializationSettings(android: androidSettings);
    await _notificationsPlugin.initialize(settings);
  }

  static Future<void> showCriticalAlert(String projectName, double deviation) async {
    const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'critical_alerts',
      'Critical System Alerts',
      channelDescription: 'Alerts for high-risk project deviations',
      importance: Importance.max,
      priority: Priority.high,
      color: Color(0xFFFF0000),
    );

    const NotificationDetails details = NotificationDetails(android: androidDetails);

    await _notificationsPlugin.show(
      DateTime.now().millisecond,
      'CRITICAL: $projectName',
      'Resource deviation reached ${(deviation * 100).toStringAsFixed(1)}%. Immediate audit required.',
      details,
    );
  }
}
