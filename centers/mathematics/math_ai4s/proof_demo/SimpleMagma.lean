-- SimpleMagma.lean
-- Δ的第一个可验证数学证明案例
-- 证明：基本逻辑性质和归纳类型定理

-- 示例：二元magma（2元素集合）
inductive TwoElement
  | a
  | b

-- 证明：二元类型是穷尽的（任何元素只能是a或b）
theorem two_element_exhaustive (x : TwoElement) : x = TwoElement.a ∨ x = TwoElement.b := by
  cases x
  · left; rfl
  · right; rfl

-- 证明：自然数加零是恒等操作
theorem my_add_zero (n : Nat) : n + 0 = n := by
  rfl

-- 证明：排中律的一个特例（True或任何命题）
theorem true_or_any (p : Prop) : True ∨ p := by
  left
  trivial

-- 证明：蕴含的自反性
theorem my_implies_refl (p : Prop) : p → p := by
  intro hp
  exact hp

-- 证明：合取的交换律
theorem my_and_comm (p q : Prop) : p ∧ q → q ∧ p := by
  intro h
  cases h with
  | intro hp hq =>
    constructor
    · exact hq
    · exact hp
