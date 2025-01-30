# 🌟 2D Physics Particle Simulator

A captivating physics simulation that brings particle dynamics to life! Watch as particles collide, spin, and interact in a beautiful display of classical mechanics.

![Physics Simulation Demo](demo.gif) *(Demo gif to be added)*

## ✨ Features

- 🎯 Interactive 1000x1000 pixel simulation space
- 🔮 100 particles with random sizes and velocities
- 🌈 Dynamic color visualization based on kinetic energy
- 🎨 Real-time particle visualization with rotation indicators
- 🎮 Interactive controls for physics parameters

## 🚀 Quick Start

1. **Prerequisites**
   - Python 3.x
   - pip (Python package manager)

2. **Installation**
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd physics-simulator

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Run the Simulation**
   ```bash
   python app.py
   ```

## 🎮 Controls

- `Left Click`: Add new particles
- `SPACE`: Pause/Resume simulation
- `R`: Reset the simulation
- `F`: Toggle friction
- `G`: Toggle gravity
- `Close Window`: Exit simulation

## 🔬 The Physics Behind It

### Particle Properties
- 🔄 Random radius (10-30 pixels)
- ⚖️ Mass proportional to area (m = πr²)
- 💫 Random initial velocity and angular velocity

### Energy Visualization
- 🌊 Blue: Low kinetic energy
- ⚪ White: Average energy
- 🔴 Red: High energy

### Physics Components
1. **Kinetic Energy** (KE)
   - Linear KE = ½mv²
   - Rotational KE = ½Iω²
   - Total KE = Linear KE + Rotational KE

2. **Collisions**
   - Perfectly elastic (e = 1.0)
   - Energy and momentum are conserved

3. **Optional Forces**
   - 🌍 Gravity (981 pixels/s² ≈ 9.81 m/s²)
   - 🎢 Friction (coefficient = 0.1)

## 🛠️ Technical Stack

- **Pygame**: Graphics rendering and user input
- **Pymunk**: Physics engine (based on Chipmunk2D)
- **Python**: Core programming language

## 📊 System Requirements

- Python 3.x
- Minimum 2GB RAM
- Basic graphics card for Pygame
- Screen resolution > 1000x1000 pixels

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 🐛 Known Issues

- None reported yet! Feel free to open an issue if you find any.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Pygame community
- Pymunk developers
- Physics teachers everywhere

---

Made with 💖 by [Your Name]

*Note: This is an educational project demonstrating classical mechanics principles through interactive simulation.*
