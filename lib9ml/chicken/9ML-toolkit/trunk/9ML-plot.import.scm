;;;; 9ML-plot.import.scm - GENERATED BY CHICKEN 4.8.0rc4 -*- Scheme -*-

(eval '(import
         scheme
         chicken
         9ML-eval
         object-graph
         signal-diagram
         (only srfi-1 fold combine every concatenate list-tabulate)
         (only data-structures intersperse string-intersperse ->string)
         (only extras fprintf pp)
         (only utils system*)
         (only files make-pathname pathname-directory pathname-file)))
(##sys#register-compiled-module
  '9ML-plot
  (list)
  '((plot-verbose . 9ML-plot#plot-verbose)
    (plot-ivp . 9ML-plot#plot-ivp)
    (plot-diagram . 9ML-plot#plot-diagram)
    (html-report . 9ML-eval#html-report))
  (list)
  (list))

;; END OF FILE
