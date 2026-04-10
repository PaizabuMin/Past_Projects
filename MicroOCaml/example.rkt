#lang racket
(define (false x) #f)
(define (id x) x)
(with-handlers ([false id])
  (raise 5))
