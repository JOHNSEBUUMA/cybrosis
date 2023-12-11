/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import session from 'web.session';

export const EFRISPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            var self = this;
			if(this.env.pos.config.cash_rounding) {
                if(!this.env.pos.get_order().check_paymentlines_rounding()) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Rounding error in payment lines'),
                        body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                    });
                    return;
                }
            }
            if (await this._isOrderValid(isForceValidate)) {
                // remove pending payments before finalizing the validation
                for (let line of this.paymentLines) {
                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                }
//                await this._finalizeValidation();
                var efris_enable = this.env.pos.company.efris_enable
                console.log('QQQQQQQQQQQQQQQ',efris_enable)
                var login_tin =  this.env.pos.company.login_tin
                var device_no =  this.env.pos.company.device_no
                var api_url =  this.env.pos.company.api_url
                if (!efris_enable){
						this.showPopup('ErrorPopup',{
							'title': this.env._t('EFRIS Authentication Failed'),
							'body': this.env._t('Kindly ensure proper configuration of the EFRIS authentication details.!!!'),
						});
					}
            }
        }
    };
Registries.Component.extend(PaymentScreen, EFRISPaymentScreen);

