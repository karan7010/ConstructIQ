import 'package:flutter/material.dart';
import '../utils/design_tokens.dart';

class DFPill extends StatelessWidget {
  final String label;
  final String severity;

  const DFPill({
    super.key,
    required this.label,
    required this.severity,
  });

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color textColor;

    switch (severity.toLowerCase()) {
      case 'critical':
        bgColor = DFColors.criticalBg;
        textColor = DFColors.critical;
        break;
      case 'warning':
        bgColor = DFColors.warningBg;
        textColor = DFColors.warning;
        break;
      case 'normal':
      case 'success':
        bgColor = DFColors.normalBg;
        textColor = DFColors.normal;
        break;
      case 'info':
      case 'active':
        bgColor = DFColors.primaryLight;
        textColor = DFColors.primary;
        break;
      default:
        bgColor = DFColors.divider;
        textColor = DFColors.textSecondary;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label.toUpperCase(),
        style: DFTextStyles.caption.copyWith(
          color: textColor,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
