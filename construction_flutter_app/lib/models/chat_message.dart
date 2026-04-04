enum MessageRole { user, assistant }

class ChatMessage {
  final String text;
  final MessageRole role;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.role,
    required this.timestamp,
  });
}
