#pragma once
#include "llk_param_structs.h"

#include "ckernel_include.h"
#include "ckernel_template.h"
#include <type_traits>

#include "cmath_common.h"
#include "llk_math_common.h"
#include "llk_format_conversions.h"
#include "ckernel_globals.h"
#include "ckernel_sfpu.h"

using namespace ckernel;
template <SfpuType sfpu_type>
void static_assert_sfpu_type_dependent() {
    static_assert(sfpu_type == SfpuType::unused, "sfpu_type exception");
}
// local function declarations
inline void eltwise_unary_sfpu_configure_addrmod(){
    // NOTE: this kernel is typically used in conjunction with
    //       A2D, which is using ADDR_MOD_0 and ADDR_MOD_2, so use one
    //       that doesn't conflict!
    addr_mod_t{
        .srca = {.incr = 0},
        .srcb = {.incr = 0},
        .dest = {.incr = 0},
    }.set(ADDR_MOD_3);
}
inline void eltwise_unary_sfpu_configure_mop();

template <SfpuType sfpu_op, bool APPROXIMATE, DstSync Dst = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu(
    uint dst_index,
    uint param0 = 0,
    uint param1 = 0,
    uint param2 = 0,
    uint param3 = 0,
    uint param4 = 0,
    uint param5 = 0) {
    TTI_STALLWAIT(p_stall::STALL_SFPU, p_stall::MATH);
    if constexpr ((Dst == DstSync::SyncTile16) || (Dst == DstSync::SyncTile2)) {
        math::set_dst_write_addr<DstTileLayout::Default, DstTileShape::Tile32x32>(math_sync_tile_dst_index);
    } else {
        math::set_dst_write_addr<DstTileLayout::Default, DstTileShape::Tile32x32>(dst_index);
    }
#pragma GCC unroll 0
    for (int face = 0; face < 4; face++) {
        sfpu::calculate_sfpu<sfpu_op, APPROXIMATE>(param0, param1, param2, param3, param4, param5);
        TTI_SETRWC(p_setrwc::CLR_NONE, p_setrwc::CR_D, 8, 0, 0, p_setrwc::SET_D);
        TTI_SETRWC(p_setrwc::CLR_NONE, p_setrwc::CR_D, 8, 0, 0, p_setrwc::SET_D);
    }
    math::clear_dst_reg_addr();
}

template <SfpuType sfpu_op, bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_init(
    uint param0 = 0, uint param1 = 0, uint param2 = 0, uint param3 = 0, uint param4 = 0, uint param5 = 0) {
    eltwise_unary_sfpu_configure_addrmod();
    if constexpr (sfpu_op == SfpuType::dropout) {
        sfpu::sfpu_init<APPROXIMATE>(sfpu_op, param2);
    } else {
        sfpu::sfpu_init<APPROXIMATE>(sfpu_op);
    }
    math::reset_counters(p_setrwc::SET_ABD_F);
}

// New LLK SFPU APIs

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_exponential(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::exponential, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_exponential_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::exponential, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_sqrt(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::sqrt, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_sqrt_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::sqrt, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_gelu(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::gelu, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_gelu_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::gelu, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_gelu_derivative(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::gelu_derivative, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_gelu_derivative_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::gelu_derivative, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_reciprocal(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::reciprocal, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_reciprocal_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::reciprocal, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_log(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::log, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_log_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::log, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_log_with_base(uint dst_index,uint base_scale) {
    llk_math_eltwise_unary_sfpu<SfpuType::log_with_base, APPROXIMATE, dst_sync>(dst_index,base_scale);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_log_with_base_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::log_with_base, APPROXIMATE>();
}


template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_tanh(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::tanh, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_tanh_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::tanh, APPROXIMATE>();
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_sin_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::sine, APPROXIMATE>();
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_cos_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::cosine, APPROXIMATE>();
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_sin(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::sine, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_cos(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::cosine, APPROXIMATE, dst_sync>(dst_index);
}

//square
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_square(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::square, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_square_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::square, APPROXIMATE>();
}

//abs
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_abs(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::abs, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_abs_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::abs, APPROXIMATE>();
}

//sign
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_sign(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::sign, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_sign_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::sign, APPROXIMATE>();
}

template <DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_dropout(uint dst_index, int integer_dropout, int scale_factor) {
    constexpr bool dont_care = false;
    llk_math_eltwise_unary_sfpu<SfpuType::dropout, dont_care, dst_sync>(dst_index, integer_dropout, scale_factor);
}

inline void llk_math_eltwise_unary_sfpu_dropout_init(uint seed = 0) {
    constexpr bool dont_care = false;
    constexpr uint dont_care_param = 0;

    llk_math_eltwise_unary_sfpu_init<SfpuType::dropout, dont_care>(dont_care_param, dont_care_param, seed);
}

template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_sigmoid(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::sigmoid, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_sigmoid_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::sigmoid, APPROXIMATE>();
}

//EQZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_eqz(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::equal_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_eqz_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::equal_zero, APPROXIMATE>();
}

//NEZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_nez(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::not_equal_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_nez_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::not_equal_zero, APPROXIMATE>();
}

//LTZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_ltz(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::less_than_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_ltz_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::less_than_zero, APPROXIMATE>();
}

//GTZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_gtz(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::greater_than_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_gtz_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::greater_than_zero, APPROXIMATE>();
}

//LEZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_lez(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::less_than_equal_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_lez_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::less_than_equal_zero, APPROXIMATE>();
}

//GEZ
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_gez(uint dst_index) {
    llk_math_eltwise_unary_sfpu<SfpuType::greater_than_equal_zero, APPROXIMATE, dst_sync>(dst_index);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_gez_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::greater_than_equal_zero, APPROXIMATE>();
}

//RELU MAX
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_relu_max(uint dst_index,uint param) {
    llk_math_eltwise_unary_sfpu<SfpuType::relu_max, APPROXIMATE, dst_sync>(dst_index,param);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_relu_max_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::relu_max, APPROXIMATE>();
}

//RELU MIN
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_relu_min(uint dst_index,uint param) {
    llk_math_eltwise_unary_sfpu<SfpuType::relu_min, APPROXIMATE, dst_sync>(dst_index,param);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_relu_min_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::relu_min, APPROXIMATE>();
}

//Power: y = x ^ (const param0)
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_power(uint dst_index,uint param) {
    llk_math_eltwise_unary_sfpu<SfpuType::power, APPROXIMATE, dst_sync>(dst_index,param);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_power_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::power, APPROXIMATE>();
}

//Leaky Relu
template <bool APPROXIMATE, DstSync dst_sync = DstSync::SyncFull>
inline void llk_math_eltwise_unary_sfpu_leaky_relu(uint dst_index,uint param0) {
    llk_math_eltwise_unary_sfpu<SfpuType::lrelu, APPROXIMATE, dst_sync>(dst_index,param0);
}

template <bool APPROXIMATE>
inline void llk_math_eltwise_unary_sfpu_leaky_relu_init() {
    llk_math_eltwise_unary_sfpu_init<SfpuType::lrelu, APPROXIMATE>();
}
