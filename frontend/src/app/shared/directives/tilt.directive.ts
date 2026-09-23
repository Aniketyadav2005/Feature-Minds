import { Directive, ElementRef, HostListener, Input, Renderer2 } from '@angular/core';

/**
 * Lightweight pointer-tracking 3D tilt effect. Attach as `appTilt` to any
 * card-like element for the "wow" 3D hover feel used across the app
 * (auth cards, stat cards, result cards).
 */
@Directive({
  selector: '[appTilt]',
  standalone: true,
})
export class TiltDirective {
  @Input() tiltMax = 8; // degrees
  @Input() tiltScale = 1.02;

  constructor(private el: ElementRef<HTMLElement>, private renderer: Renderer2) {
    this.renderer.setStyle(this.el.nativeElement, 'transform-style', 'preserve-3d');
    this.renderer.setStyle(this.el.nativeElement, 'will-change', 'transform');
  }

  @HostListener('pointermove', ['$event'])
  onPointerMove(e: PointerEvent): void {
    const rect = this.el.nativeElement.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width; // 0..1
    const y = (e.clientY - rect.top) / rect.height; // 0..1
    const rotateY = (x - 0.5) * 2 * this.tiltMax;
    const rotateX = (0.5 - y) * 2 * this.tiltMax;

    this.renderer.setStyle(
      this.el.nativeElement,
      'transform',
      `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${this.tiltScale})`
    );
  }

  @HostListener('pointerleave')
  onPointerLeave(): void {
    this.renderer.setStyle(
      this.el.nativeElement,
      'transform',
      'perspective(900px) rotateX(0deg) rotateY(0deg) scale(1)'
    );
  }
}