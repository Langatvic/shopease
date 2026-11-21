// Global JS helpers
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash messages after 4s
  document.querySelectorAll('.alert-dismissible').forEach(el => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      alert.close();
    }, 4000);
  });
});