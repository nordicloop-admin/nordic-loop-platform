// Example of using EmailJS with the password reset API
// This is a demonstration file showing how to integrate EmailJS with our backend

// First, include EmailJS in your HTML:
// <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
// <script type="text/javascript">
//   (function() {
//     emailjs.init("YOUR_USER_ID"); // Replace with your EmailJS user ID
//   })();
// </script>

/**
 * Request password reset function
 * This function calls our backend API and then uses EmailJS to send the OTP
 */
async function requestPasswordReset(email) {
  try {
    // Step 1: Call our backend API to generate an OTP
    const response = await fetch('/api/users/request-password-reset/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        use_emailjs: true // This flag tells our backend to return the OTP
      }),
    });

    const data = await response.json();
    
    if (!data.success) {
      console.error('Failed to generate OTP:', data.error);
      return {
        success: false,
        message: data.error || 'Failed to generate OTP'
      };
    }

    // Step 2: Send the OTP via EmailJS
    const emailjsResponse = await emailjs.send(
      'YOUR_SERVICE_ID', // Replace with your EmailJS service ID
      'YOUR_TEMPLATE_ID', // Replace with your EmailJS template ID
      {
        to_email: data.email,
        otp: data.otp,
        expiry_time: '30 minutes',
        // Add any other template variables you need
      }
    );

    console.log('Email sent successfully:', emailjsResponse);
    return {
      success: true,
      message: 'Password reset OTP has been sent to your email'
    };
  } catch (error) {
    console.error('Error in password reset process:', error);
    return {
      success: false,
      message: 'Failed to process password reset request'
    };
  }
}

/**
 * Verify OTP function
 * This function calls our backend API to verify the OTP
 */
async function verifyOtp(email, otp) {
  try {
    const response = await fetch('/api/users/verify-otp/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        otp: otp
      }),
    });

    const data = await response.json();
    
    if (!data.success) {
      console.error('Failed to verify OTP:', data.error);
      return {
        success: false,
        message: data.error || 'Failed to verify OTP'
      };
    }

    return {
      success: true,
      message: 'OTP verified successfully',
      token: data.token
    };
  } catch (error) {
    console.error('Error verifying OTP:', error);
    return {
      success: false,
      message: 'Failed to verify OTP'
    };
  }
}

/**
 * Reset password function
 * This function calls our backend API to reset the password
 */
async function resetPassword(email, token, newPassword, confirmPassword) {
  try {
    const response = await fetch('/api/users/reset-password/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        token: token,
        new_password: newPassword,
        confirm_password: confirmPassword
      }),
    });

    const data = await response.json();
    
    if (!data.success) {
      console.error('Failed to reset password:', data.error);
      return {
        success: false,
        message: data.error || 'Failed to reset password'
      };
    }

    return {
      success: true,
      message: 'Password has been reset successfully'
    };
  } catch (error) {
    console.error('Error resetting password:', error);
    return {
      success: false,
      message: 'Failed to reset password'
    };
  }
}

// Example usage in a form submission handler
document.addEventListener('DOMContentLoaded', function() {
  // Request Password Reset Form
  const requestForm = document.getElementById('request-password-form');
  if (requestForm) {
    requestForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const email = document.getElementById('email').value;
      const result = await requestPasswordReset(email);
      
      // Show result to user
      alert(result.message);
      
      if (result.success) {
        // Redirect to OTP verification page
        window.location.href = '/static/password_reset/verify_otp.html?email=' + encodeURIComponent(email);
      }
    });
  }
  
  // Verify OTP Form
  const verifyForm = document.getElementById('verify-otp-form');
  if (verifyForm) {
    verifyForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const email = new URLSearchParams(window.location.search).get('email');
      const otp = document.getElementById('otp').value;
      const result = await verifyOtp(email, otp);
      
      // Show result to user
      alert(result.message);
      
      if (result.success) {
        // Redirect to reset password page with token
        window.location.href = '/static/password_reset/reset_password.html?email=' + 
          encodeURIComponent(email) + '&token=' + encodeURIComponent(result.token);
      }
    });
  }
  
  // Reset Password Form
  const resetForm = document.getElementById('reset-password-form');
  if (resetForm) {
    resetForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      const urlParams = new URLSearchParams(window.location.search);
      const email = urlParams.get('email');
      const token = urlParams.get('token');
      const newPassword = document.getElementById('new-password').value;
      const confirmPassword = document.getElementById('confirm-password').value;
      
      const result = await resetPassword(email, token, newPassword, confirmPassword);
      
      // Show result to user
      alert(result.message);
      
      if (result.success) {
        // Redirect to login page
        window.location.href = '/login';
      }
    });
  }
});
