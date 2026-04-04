const functions = require("firebase-functions");
const admin = require("firebase-admin");
admin.initializeApp();

/**
 * Phase 2+: Set user role in Firebase Auth custom claims.
 * Triggered manually by Admin via callable function.
 */
exports.setUserRole = functions.https.onCall(async (data, context) => {
  // Check if requester is admin
  // if (context.auth.token.role !== 'admin') { ... }

  const { uid, role } = data;
  
  const validRoles = ['admin', 'manager', 'engineer', 'owner'];
  if (!validRoles.includes(role)) {
    throw new functions.https.HttpsError("invalid-argument", `Role ${role} is not valid.`);
  }

  try {
    await admin.auth().setCustomUserClaims(uid, { role });
    await admin.firestore().collection("users").doc(uid).update({
      role: role
    });
    return { status: "success", message: `Role ${role} assigned to user ${uid}` };
  } catch (error) {
    throw new functions.https.HttpsError("internal", error.message);
  }
});
