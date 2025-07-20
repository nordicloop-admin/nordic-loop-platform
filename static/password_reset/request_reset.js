document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('requestResetForm');
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const submitBtn = document.getElementById('submitBtn');
    const successMessage = document.getElementById('successMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset error messages
        emailError.textContent = '';
        successMessage.textContent = '';
        
        // Validate email
        const email = emailInput.value.trim();
        if (!email) {
            emailError.textContent = 'Email is required';
            return;
        }
        
        if (!isValidEmail(email)) {
            emailError.textContent = 'Please enter a valid email address';
            return;
        }
        
        // Disable button and show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        
        try {
            // Send request to API
            const response = await fetch('/api/users/request-password-reset/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Success - show message and redirect after delay
                successMessage.textContent = data.message || 'OTP sent successfully. Redirecting to verification page...';
                
                // Store email in session storage for next step
                sessionStorage.setItem('resetEmail', email);
                
                // Redirect to OTP verification page after 2 seconds
                setTimeout(() => {
                    window.location.href = 'verify_otp.html';
                }, 2000);
            } else {
                // Error
                emailError.textContent = data.error || 'Failed to send OTP. Please try again.';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send Reset OTP';
            }
        } catch (error) {
            console.error('Error:', error);
            emailError.textContent = 'An error occurred. Please try again later.';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Reset OTP';
        }
    });
    
    // Email validation function
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
});
