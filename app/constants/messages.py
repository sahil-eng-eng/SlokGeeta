"""All user-facing and internal messages centralized here."""

AUTH_MESSAGES = {
    "EMAIL_ALREADY_REGISTERED": "Email already registered",
    "USERNAME_ALREADY_TAKEN": "Username already taken",
    "INVALID_CREDENTIALS": "Invalid email or password",
    "ACCOUNT_NOT_VERIFIED": "Account not verified. Please check your email for OTP.",
    "INVALID_TOKEN": "Invalid or expired token",
    "USER_NOT_FOUND": "User not found",
    "MISSING_AUTH_HEADER": "Missing or invalid authorization header",
    "INVALID_TOKEN_PAYLOAD": "Invalid token payload",
    "ACCOUNT_DEACTIVATED": "Account is deactivated",
    "REGISTRATION_SUCCESS": "Registration successful. Check your email for verification.",
    "EMAIL_VERIFIED": "Email verified successfully",
    "LOGIN_SUCCESS": "Login successful",
    "GOOGLE_AUTH_SUCCESS": "Google auth successful",
    "TOKEN_REFRESHED": "Token refreshed",
    "LOGGED_OUT": "Logged out successfully",
    "ALL_SESSIONS_LOGGED_OUT": "All sessions logged out",
    "RESET_LINK_SENT": "If the email exists, a reset link has been sent.",
    "PASSWORD_RESET_SUCCESS": "Password reset successfully",
    "PASSWORD_CHANGED": "Password changed successfully",
    "OTP_RESENT": "If the email exists and is unverified, a new OTP has been sent.",
    "PROFILE_RETRIEVED": "User profile retrieved",
    "PROFILE_UPDATED": "Profile updated",
    "AVATAR_UPLOADED": "Avatar uploaded",
}

BOOK_MESSAGES = {
    "NOT_FOUND": "Book not found",
    "FORBIDDEN": "You do not have permission to access this book",
    "CREATED": "Book created",
    "UPDATED": "Book updated",
    "DELETED": "Book deleted",
    "RETRIEVED": "Book retrieved",
    "LIST_RETRIEVED": "Books retrieved",
    "COVER_UPLOADED": "Cover uploaded",
    "CANNOT_MAKE_PRIVATE": "Cannot set book to private: one or more shloks or meanings are still shared with users. Revoke all sharing first.",
}

SHLOK_MESSAGES = {
    "NOT_FOUND": "Shlok not found",
    "FORBIDDEN": "You do not have permission to access this shlok",
    "CREATED": "Shlok created",
    "UPDATED": "Shlok updated",
    "DELETED": "Shlok deleted",
    "RETRIEVED": "Shlok retrieved",
    "LIST_RETRIEVED": "Shloks retrieved",
    "AUDIO_UPLOADED": "Audio uploaded",
    "RELATED_RETRIEVED": "Related shloks retrieved",
    "CROSS_REF_ADDED": "Cross reference added",
    "CROSS_REFS_RETRIEVED": "Cross references retrieved",
    "CANNOT_MAKE_PRIVATE": "Cannot set shlok to private: one or more meanings are still shared with users. Revoke all sharing first.",
}

GENERAL_MESSAGES = {
    "HEALTH_OK": "ok",
    "INTERNAL_ERROR": "Internal server error",
}

MEANING_MESSAGES = {
    "NOT_FOUND": "Meaning not found",
    "FORBIDDEN": "You do not have permission to modify this meaning",
    "CREATED": "Meaning created",
    "UPDATED": "Meaning updated",
    "DELETED": "Meaning deleted",
    "RETRIEVED": "Meanings retrieved",
    "VOTED": "Vote recorded",
    "CANNOT_MAKE_PRIVATE": "Cannot set meaning to private: one or more replies are still shared with users. Revoke all sharing first.",
}

FRIEND_MESSAGES = {
    "REQUEST_SENT": "Friend request sent",
    "REQUEST_ACCEPTED": "Friend request accepted",
    "REQUEST_REJECTED": "Friend request rejected",
    "REQUEST_CANCELLED": "Friend request cancelled",
    "ALREADY_FRIENDS": "You are already friends",
    "REQUEST_ALREADY_SENT": "Friend request already sent",
    "REQUEST_NOT_FOUND": "Friend request not found",
    "FRIEND_NOT_FOUND": "Friend not found",
    "CANNOT_FRIEND_SELF": "You cannot send a friend request to yourself",
    "UNFRIENDED": "Friend removed",
    "FRIENDS_RETRIEVED": "Friends retrieved",
    "SEARCH_RETRIEVED": "Users retrieved",
}

CHAT_MESSAGES = {
    "NOT_FRIENDS": "You can only chat with friends",
    "MESSAGE_SENT": "Message sent",
    "MESSAGES_RETRIEVED": "Messages retrieved",
    "CONVERSATIONS_RETRIEVED": "Conversations retrieved",
    "MESSAGE_DELETED": "Message deleted",
    "MESSAGE_EDITED": "Message updated",
    "MESSAGE_NOT_FOUND": "Message not found",
    "MESSAGE_FORBIDDEN": "You can only modify your own messages",
}

LINK_MESSAGES = {
    "CREATED": "Shareable link generated",
    "NOT_FOUND": "Link not found or expired",
    "RETRIEVED": "Link resolved",
}

PERMISSION_MESSAGES = {
    "GRANTED": "Permissions granted",
    "UPDATED": "Permissions updated",
    "REVOKED": "Permissions revoked",
    "RETRIEVED": "Permissions retrieved",
    "FORBIDDEN": "You do not have permission to manage permissions for this entity",
}

CONTENT_REQUEST_MESSAGES = {
    "CREATED": "Request submitted",
    "REQUEST_CREATED": "Request submitted",
    "APPROVED": "Request approved",
    "REJECTED": "Request rejected",
    "NOT_FOUND": "Request not found",
    "FORBIDDEN": "You do not have permission to review this request",
    "RETRIEVED": "Requests retrieved",
    "REQUESTS_RETRIEVED": "Requests retrieved",
    "REQUEST_REVIEWED": "Request reviewed",
}
