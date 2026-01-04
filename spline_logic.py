import numpy as np
import io
import matplotlib.pyplot as plt

class CubicSplineSolver:
    def __init__(self, x, y):
        self.x = np.array(x, dtype=float)
        self.y = np.array(y, dtype=float)
        self.n = len(x) - 1
        self.a = self.y.copy()
        self.b = np.zeros(self.n)
        self.c = np.zeros(self.n + 1)
        self.d = np.zeros(self.n)
        self.steps = []
        
    def solve(self):
        # Step 1: Calculate h
        h = self.x[1:] - self.x[:-1]
        self.steps.append(f"1. محاسبه فاصله گره‌ها (h):\n{h}")
        
        # Step 2: Form Tridiagonal Matrix A and vector B
        # System: A * c = B
        # Dimension is (n-1) unknowns for Natural Spline (c_0 = c_n = 0)
        
        alpha = np.zeros(self.n) # RHS of the system
        for i in range(1, self.n):
            term1 = (3/h[i]) * (self.a[i+1] - self.a[i])
            term2 = (3/h[i-1]) * (self.a[i] - self.a[i-1])
            alpha[i] = term1 - term2
            
        self.steps.append(f"2. تشکیل سمت راست معادلات (alpha):\n{alpha[1:]}")

        # Tridiagonal System solving (Crout/Thomas algorithm)
        l = np.zeros(self.n + 1)
        mu = np.zeros(self.n + 1)
        z = np.zeros(self.n + 1)
        
        l[0] = 1.0
        mu[0] = 0.0
        z[0] = 0.0
        
        self.steps.append("3. حل سیستم سه قطری برای یافتن c (مشتق دوم/2):")
        
        for i in range(1, self.n):
            l[i] = 2 * (h[i-1] + h[i]) - h[i-1] * mu[i-1]
            mu[i] = h[i] / l[i]
            z[i] = (alpha[i] - h[i-1] * z[i-1]) / l[i]
            
        l[self.n] = 1.0
        z[self.n] = 0.0
        self.c[self.n] = 0.0
        
        # Back substitution
        for j in range(self.n - 1, -1, -1):
            self.c[j] = z[j] - mu[j] * self.c[j+1]
            
        self.steps.append(f"مقادیر c بدست آمد:\n{self.c}")

        # Step 3: Calculate b and d
        for i in range(self.n):
            self.b[i] = (self.a[i+1] - self.a[i]) / h[i] - h[i] * (self.c[i+1] + 2 * self.c[i]) / 3
            self.d[i] = (self.c[i+1] - self.c[i]) / (3 * h[i])
            
        self.steps.append("4. محاسبه ضرایب نهایی a, b, c, d برای هر بازه.")
        
        results = []
        for i in range(self.n):
            results.append(f"Interval [{self.x[i]}, {self.x[i+1]}]:\n"
                           f"S(x) = {self.a[i]:.4f} + {self.b[i]:.4f}(x-{self.x[i]}) + "
                           f"{self.c[i]:.4f}(x-{self.x[i]})^2 + {self.d[i]:.4f}(x-{self.x[i]})^3")
        
        return "\n\n".join(results)

    def get_steps(self):
        return "\n\n".join(self.steps)

    def plot_spline(self):
        plt.figure(figsize=(10, 6))
        plt.scatter(self.x, self.y, color='red', label='Points')
        
        for i in range(self.n):
            x_vals = np.linspace(self.x[i], self.x[i+1], 100)
            y_vals = self.a[i] + self.b[i]*(x_vals-self.x[i]) + \
                     self.c[i]*(x_vals-self.x[i])**2 + self.d[i]*(x_vals-self.x[i])**3
            plt.plot(x_vals, y_vals, 'b-', label='Spline' if i == 0 else "")
            
        plt.title('Cubic Spline Interpolation')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True)
        plt.legend()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf

class ParametricSplineSolver:
    def __init__(self, x, y):
        self.x = np.array(x, dtype=float)
        self.y = np.array(y, dtype=float)
        self.n = len(x)
        # Create parameter t (e.g., chord length or just index)
        # Using index 0, 1, 2... for simplicity, or chord length usually better.
        # Let's use simple index for educational clarity unless distance is preferred.
        # Distance (Chord Length) is better for drawing shapes smoothly.
        self.t = np.zeros(self.n)
        for i in range(1, self.n):
            dist = np.sqrt((self.x[i]-self.x[i-1])**2 + (self.y[i]-self.y[i-1])**2)
            self.t[i] = self.t[i-1] + dist
            
        # If t is all zero (duplicate points), fix it
        if self.t[-1] == 0:
            self.t = np.arange(self.n, dtype=float)

        self.spline_x = CubicSplineSolver(self.t, self.x)
        self.spline_y = CubicSplineSolver(self.t, self.y)
        
    def solve(self):
        res_x = self.spline_x.solve()
        res_y = self.spline_y.solve()
        return (f"--- معادلات x(t) ---\n{res_x}\n\n"
                f"--- معادلات y(t) ---\n{res_y}")
                
    def get_steps(self):
        return (f"--- مراحل حل x(t) ---\n{self.spline_x.get_steps()}\n\n"
                f"--- مراحل حل y(t) ---\n{self.spline_y.get_steps()}")

    def plot_spline(self):
        # We need to solve first to get coefficients
        self.spline_x.solve()
        self.spline_y.solve()
        
        plt.figure(figsize=(8, 8)) # Square figure for better geometry
        plt.scatter(self.x, self.y, color='red', label='Points')
        # Annotate points order
        for i, (px, py) in enumerate(zip(self.x, self.y)):
            plt.text(px, py, str(i), fontsize=9)

        # Plot segment by segment
        # Since spline_x and spline_y are just CubicSplineSolvers, we iterate their intervals
        for i in range(self.n - 1):
            t_start = self.t[i]
            t_end = self.t[i+1]
            t_vals = np.linspace(t_start, t_end, 50)
            
            # Evaluate x(t)
            # S_x(t) = a + b(t-ti) + c(t-ti)^2 + d(t-ti)^3
            # spline_x coefficients at index i
            ax, bx, cx, dx = self.spline_x.a[i], self.spline_x.b[i], self.spline_x.c[i], self.spline_x.d[i]
            x_vals = ax + bx*(t_vals-t_start) + cx*(t_vals-t_start)**2 + dx*(t_vals-t_start)**3
            
            # Evaluate y(t)
            ay, by, cy, dy = self.spline_y.a[i], self.spline_y.b[i], self.spline_y.c[i], self.spline_y.d[i]
            y_vals = ay + by*(t_vals-t_start) + cy*(t_vals-t_start)**2 + dy*(t_vals-t_start)**3
            
            plt.plot(x_vals, y_vals, 'b-', label='Parametric Spline' if i == 0 else "")

        plt.title('Parametric Cubic Spline')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.axis('equal') # Important for correct shape perception
        plt.grid(True)
        plt.legend()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf
