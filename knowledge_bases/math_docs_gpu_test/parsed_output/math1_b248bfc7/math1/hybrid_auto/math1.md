technique given by Campbell and Cantarini [5] and relying on a modified Abel lemma, we obtain a simplified proof of Yamaguchi’s $q$ -analogue, together with a new $q$ -analogue of Gosper’s identity that is inequivalent to Yamaguchi’s $q$ -analogue. We also show how a similar approach can be applied much more broadly in the construction of $q$ -analogues, as in Sections 2.1–2.3 below.

1.1. Preliminaries. The shifted factorial is such that $( x ) _ { 0 } = 1$ and $( x ) _ { n } = x ( x + 1 ) \cdots ( x + n - 1 )$ for positive integers n. Generalized hypergeometric series may then be defined so that

$$
{ } _ { r } F _ { s } \left[ \begin{array} { c } a _ { 1 } , a _ { 2 } , \ldots , a _ { r } \\ b _ { 1 } , b _ { 2 } , \ldots , b _ { s } \end{array} ; x \right] = \sum _ { n = 0 } ^ { \infty } \frac { ( a _ { 1 } ) _ { n } ( a _ { 2 } ) _ { n } \cdots ( a _ { r } ) _ { n } } { ( b _ { 1 } ) _ { n } ( b _ { 2 } ) _ { n } \cdots ( b _ { s } ) _ { n } } \frac { x ^ { n } } { n ! } ,
$$

referring to Bailey’s classic text for background [3].

For $| q | < 1$ , we recall the standard notation for $q$ -shifted factorials. For a complex number $a$ , the $q$ -shifted factorial is defined by

$$
\begin{array}{l} (a; q) _ {0} = 1, \\ (a; q) _ {n} = \prod_ {k = 0} ^ {n - 1} \left(1 - a q ^ {k}\right), \quad n \geq 1, \\ (a; q) _ {\infty} = \prod_ {k = 0} ^ {\infty} \left(1 - a q ^ {k}\right). \\ \end{array}
$$

We thus obtain a q-analogue of the shifted factorial in the sense that limq→1 (qa;q)n(1−q) n $q$ $\begin{array} { r } { \operatorname* { l i m } _ { q \to 1 } \frac { ( q ^ { a } ; q ) _ { n } } { ( 1 - q ) ^ { n } } = ( a ) _ { n } } \end{array}$ . Basic hypergeometric series of the form ${ } _ { r } \phi _ { r - 1 }$ may then be defined so that

$$
{ } _ { r } \phi _ { r - 1 } \left[ \begin{array} { c } a _ { 1 } , a _ { 2 } , \ldots , a _ { r } \\ b _ { 1 } , b _ { 2 } , \ldots , b _ { r - 1 } \end{array} ; q , x \right] = \sum _ { n = 0 } ^ { \infty } \frac { ( a _ { 1 } ; q ) _ { n } ( a _ { 2 } ; q ) _ { n } \cdots ( a _ { r } ; q ) _ { n } } { ( q ; q ) _ { n } ( b _ { 1 } ; q ) _ { n } ( b _ { 2 } ; q ) _ { n } \cdots ( b _ { r - 1 } ; q ) _ { n } } x ^ { n } ,
$$

where it is assumed that $| q | < 1$ . For brevity, we also write

$$
\left[ \begin{array}{c} a _ {1}, a _ {2}, \dots , a _ {r} \\ b _ {1}, b _ {2}, \dots , b _ {s} \end{array} ; q \right] _ {n} = \frac {(a _ {1} ; q) _ {n} (a _ {2} ; q) _ {n} \cdots (a _ {r} ; q) _ {n}}{(b _ {1} ; q) _ {n} (b _ {2} ; q) _ {n} \cdots (b _ {s} ; q) _ {n}}
$$

and

$$
\left[ \begin{array}{c} a _ {1}, a _ {2}, \ldots , a _ {r} \\ b _ {1}, b _ {2}, \ldots , b _ {s} \end{array} ; q \right] _ {\infty} = \frac {(a _ {1} ; q) _ {\infty} (a _ {2} ; q) _ {\infty} \cdots (a _ {r} ; q) _ {\infty}}{(b _ {1} ; q) _ {\infty} (b _ {2} ; q) _ {\infty} \cdots (b _ {s} ; q) _ {\infty}}.
$$

For a sequence $\left( \tau _ { n } : n \in \mathbb { N } _ { 0 } \right)$ , define the backward difference operator $\nabla$ and the forward difference operator $\Delta$ so that $\nabla \tau _ { n } = \tau _ { n } - \tau _ { n - 1 }$ and $\Delta \tau _ { n } = \tau _ { n } - \tau _ { n + 1 }$ . Being consistent with a number of research contributions from Chu et al. [8, 10, 11, 12] that have inspired our work, we let the relation

$$
\sum_ {n = 1} ^ {\infty} B _ {n} \nabla A _ {n} = \left(\lim  _ {m \rightarrow \infty} A _ {m} B _ {m + 1}\right) - A _ {0} B _ {1} + \sum_ {n = 1} ^ {\infty} A _ {n} \Delta B _ {n} \tag {3}
$$

be referred to as the modified Abel lemma on summation by parts, with the assumption that the above limit exists and that the one of the two series in (3) converges. The summation lemma in (3) together with a $q$ -version of a technique (reviewed below) based on this lemma due to Campbell and Cantarini [5] provide the keys to our main results given in Section 2 below.